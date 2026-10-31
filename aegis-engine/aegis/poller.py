"""AIS Telemetry Poller and In-Memory State Manager for Aegis-Sea."""

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Deque
import httpx
from pydantic import BaseModel, Field

from aegis.config import settings, Settings
from aegis.cable_index import CableCorridorIndex
from aegis.dispatcher import AlertDispatcher
from aegis.models import (
    ThreatAssessment,
    ThreatLevel,
    ThreatOverview,
    VesselTrackPoint,
)
from aegis.scorer import ThreatScorer

logger = logging.getLogger("aegis.poller")


class CachedVessel(BaseModel):
    """In-memory state and trajectory buffer for a tracked maritime contact."""

    mmsi: str
    name: str = "Unknown"
    imo: Optional[str] = None
    ship_type: Optional[str] = None
    lat: float
    lon: float
    sog: float
    cog: float
    heading: Optional[float] = None
    last_seen_epoch: float
    entered_corridor_epoch: Optional[float] = None
    track_history: List[VesselTrackPoint] = Field(default_factory=list)
    latest_assessment: Optional[ThreatAssessment] = None


class AISPoller:
    """Polls upstream AIS live feed, maintains track buffers, and coordinates threat scoring."""

    def __init__(
        self,
        scorer: ThreatScorer,
        config: Optional[Settings] = None,
        dispatcher: Optional[AlertDispatcher] = None,
        max_track_samples: int = 64,
    ):
        self.scorer = scorer
        self.config = config or settings
        self.dispatcher = dispatcher
        self.max_track_samples = max_track_samples
        self._vessels: Dict[str, CachedVessel] = {}
        self._track_buffers: Dict[str, Deque[VesselTrackPoint]] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._last_poll_epoch: Optional[float] = None
        self._last_poll_status: str = "INITIALIZING"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self):
        """Cleanly releases network client and terminates background polling."""
        self._is_running = False
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def ingest_vessel_telemetry(
        self,
        mmsi: str,
        lat: float,
        lon: float,
        sog: float,
        cog: float,
        heading: Optional[float] = None,
        name: str = "Unknown",
        imo: Optional[str] = None,
        ship_type: Optional[str] = None,
        timestamp_epoch: Optional[float] = None,
    ) -> ThreatAssessment:
        """Ingests a single vessel telemetry fix, updates track buffer, and assesses threat."""
        now = timestamp_epoch or datetime.now(timezone.utc).timestamp()

        # Retrieve or initialize track ring buffer
        if mmsi not in self._track_buffers:
            self._track_buffers[mmsi] = deque(maxlen=self.max_track_samples)
        buffer = self._track_buffers[mmsi]

        cached = self._vessels.get(mmsi)
        entered_corridor_epoch = cached.entered_corridor_epoch if cached else None
        last_seen = cached.last_seen_epoch if cached else now

        # Convert deque to list for scoring evaluation
        history_list = list(buffer)

        # Pre-query corridor to manage entered_corridor_epoch dwell tracking
        closest_cable = self.scorer.cable_index.get_closest_cable(
            lat=lat,
            lon=lon,
            max_distance_nm=self.config.alert_horizon_nm,
        )
        in_corridor = closest_cable is not None and closest_cable.in_alert_corridor

        if in_corridor:
            if entered_corridor_epoch is None:
                entered_corridor_epoch = now
        else:
            entered_corridor_epoch = None

        # Execute Threat Assessment
        assessment = self.scorer.score_vessel(
            mmsi=mmsi,
            lat=lat,
            lon=lon,
            sog=sog,
            cog=cog,
            heading=heading,
            name=name,
            imo=imo,
            ship_type=ship_type,
            history=history_list,
            current_time_epoch=now,
            entered_corridor_epoch=entered_corridor_epoch,
            last_seen_epoch=last_seen,
        )

        # Append new point to historical ring buffer
        buffer.append(
            VesselTrackPoint(
                lat=lat,
                lon=lon,
                sog=sog,
                cog=cog,
                timestamp_epoch=now,
            )
        )

        # Update cache
        self._vessels[mmsi] = CachedVessel(
            mmsi=mmsi,
            name=name,
            imo=imo,
            ship_type=ship_type,
            lat=lat,
            lon=lon,
            sog=sog,
            cog=cog,
            heading=heading,
            last_seen_epoch=now,
            entered_corridor_epoch=entered_corridor_epoch,
            track_history=list(buffer),
            latest_assessment=assessment,
        )

        # Automated Incident Response Dispatch Trigger
        if (
            self.dispatcher is not None
            and self.config.auto_dispatch_enabled
            and assessment.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL)
        ):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.dispatcher.dispatch(assessment))
            except RuntimeError:
                # No active event loop running (e.g., synchronous unit test)
                pass

        return assessment

    async def poll_once(self) -> int:
        """Executes a single poll cycle against the upstream Node.js live vessel endpoint."""
        now = datetime.now(timezone.utc).timestamp()
        url = f"{self.config.node_server_url.rstrip('/')}/api/vessels"
        client = await self._get_client()

        try:
            response = await client.get(url)
            if response.status_code != 200:
                logger.warning(
                    f"Upstream vessel feed returned HTTP {response.status_code}"
                )
                self._last_poll_status = f"HTTP_{response.status_code}"
                return 0

            data = response.json()
            rows = data.get("rows", [])
            count = 0

            for row in rows:
                mmsi = str(row.get("mmsi") or "").strip()
                lat = row.get("lat")
                lon = row.get("lon")
                if not mmsi or lat is None or lon is None:
                    continue

                sog = float(row.get("speed", 0.0) or 0.0)
                cog = float(row.get("course", 0.0) or 0.0)
                heading_raw = row.get("heading")
                heading = float(heading_raw) if heading_raw is not None else None
                name = row.get("name") or f"MMSI {mmsi}"
                imo = str(row.get("imo") or "") or None
                ship_type = row.get("type") or None
                epoch = float(row.get("last_position_epoch") or now)

                self.ingest_vessel_telemetry(
                    mmsi=mmsi,
                    lat=float(lat),
                    lon=float(lon),
                    sog=sog,
                    cog=cog,
                    heading=heading,
                    name=name,
                    imo=imo,
                    ship_type=ship_type,
                    timestamp_epoch=epoch,
                )
                count += 1

            self._last_poll_epoch = now
            self._last_poll_status = "OK"
            logger.info(f"Polled and assessed {count} live vessels from {url}")
            return count

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning(f"Could not reach upstream vessel feed at {url}: {exc}")
            self._last_poll_status = "UNREACHABLE"
            return 0
        except Exception as exc:
            logger.error(f"Unexpected error during AIS poll cycle: {exc}", exc_info=True)
            self._last_poll_status = "ERROR"
            return 0

    async def start_polling(self):
        """Starts the asynchronous polling background task."""
        if self._is_running:
            return
        self._is_running = True

        async def _loop():
            while self._is_running:
                try:
                    await self.poll_once()
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(self.config.poll_interval_seconds)

        self._poll_task = asyncio.create_task(_loop())

    # -------------------------------------------------------------------------
    # Query State & Overview API
    # -------------------------------------------------------------------------

    def get_assessment(self, mmsi: str) -> Optional[ThreatAssessment]:
        """Retrieves the latest ThreatAssessment for a given MMSI."""
        vessel = self._vessels.get(mmsi)
        return vessel.latest_assessment if vessel else None

    def get_all_assessments(
        self,
        min_level: Optional[ThreatLevel] = None,
        only_in_corridor: bool = False,
    ) -> List[ThreatAssessment]:
        """Returns filtered list of active threat assessments."""
        level_order = {
            ThreatLevel.NORMAL: 0,
            ThreatLevel.ADVISORY: 1,
            ThreatLevel.HIGH: 2,
            ThreatLevel.CRITICAL: 3,
        }
        min_rank = level_order.get(min_level, 0) if min_level else 0

        assessments: List[ThreatAssessment] = []
        for vessel in self._vessels.values():
            a = vessel.latest_assessment
            if not a:
                continue
            if only_in_corridor and (not a.closest_cable or not a.closest_cable.in_alert_corridor):
                continue
            if level_order.get(a.threat_level, 0) >= min_rank:
                assessments.append(a)

        # Sort descending by threat score
        assessments.sort(key=lambda x: x.threat_score, reverse=True)
        return assessments

    def get_overview(self) -> ThreatOverview:
        """Generates system-wide summary metrics for operational dashboards."""
        total = len(self._vessels)
        corridor_count = 0
        crit_count = 0
        high_count = 0
        adv_count = 0
        norm_count = 0
        active_threats: List[ThreatAssessment] = []

        for vessel in self._vessels.values():
            a = vessel.latest_assessment
            if not a:
                continue

            if a.closest_cable and a.closest_cable.in_alert_corridor:
                corridor_count += 1

            if a.threat_level == ThreatLevel.CRITICAL:
                crit_count += 1
                active_threats.append(a)
            elif a.threat_level == ThreatLevel.HIGH:
                high_count += 1
                active_threats.append(a)
            elif a.threat_level == ThreatLevel.ADVISORY:
                adv_count += 1
                active_threats.append(a)
            else:
                norm_count += 1

        active_threats.sort(key=lambda x: x.threat_score, reverse=True)

        return ThreatOverview(
            monitored_vessels_total=total,
            corridor_vessels_total=corridor_count,
            threats_critical_count=crit_count,
            threats_high_count=high_count,
            threats_advisory_count=adv_count,
            threats_normal_count=norm_count,
            threats=active_threats,
        )
