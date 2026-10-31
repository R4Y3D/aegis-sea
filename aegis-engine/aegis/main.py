"""Aegis-Sea FastAPI Cyber-Physical Threat Scoring Service."""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from aegis.config import settings
from aegis.cable_index import CableCorridorIndex
from aegis.dispatcher import AlertDispatcher
from aegis.models import (
    CableIndexStats,
    DispatchRecord,
    EvaluateRequest,
    ManualDispatchRequest,
    ThreatAssessment,
    ThreatLevel,
    ThreatOverview,
)
from aegis.poller import AISPoller
from aegis.scorer import ThreatScorer

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aegis.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes subsea cable spatial index, scoring engine, alert dispatcher, and live poller."""
    logger.info("Initializing Aegis-Sea Subsea Cable Corridor Index...")
    cable_index = CableCorridorIndex(auto_load=True)
    scorer = ThreatScorer(cable_index=cable_index, config=settings)
    dispatcher = AlertDispatcher(config=settings)
    poller = AISPoller(scorer=scorer, config=settings, dispatcher=dispatcher)

    app.state.cable_index = cable_index
    app.state.scorer = scorer
    app.state.dispatcher = dispatcher
    app.state.poller = poller

    logger.info(
        f"Aegis-Sea Engine ready with {cable_index.total_features} cables "
        f"({cable_index.total_segments} segments indexed)."
    )

    # Start live telemetry poller in background
    await poller.start_polling()

    yield

    logger.info("Shutting down Aegis-Sea background polling and resources...")
    await poller.close()


app = FastAPI(
    title="Aegis-Sea Threat Intelligence Engine",
    description=(
        "Resilient Cyber-Physical Threat Intelligence & Automated BGP/SOAR Incident "
        "Response Engine protecting 712 global submarine fiber-optic cables against "
        "maritime gray-zone sabotage and adversarial telemetry manipulation."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for God's Eye View UI and local dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """System health check and spatial index statistics."""
    poller: AISPoller = app.state.poller
    cable_index: CableCorridorIndex = app.state.cable_index
    dispatcher: AlertDispatcher = app.state.dispatcher
    return {
        "status": "healthy",
        "service": "aegis-sea-engine",
        "version": "0.1.0",
        "cables_indexed": cable_index.total_features,
        "segments_indexed": cable_index.total_segments,
        "vessels_monitored": len(poller._vessels),
        "alerts_dispatched": len(dispatcher._history),
        "poller_status": poller._last_poll_status,
        "last_poll_epoch": poller._last_poll_epoch,
    }


@app.get("/api/threats/overview", response_model=ThreatOverview, tags=["Threat Intelligence"])
async def get_threat_overview():
    """Retrieves fleet-wide threat summary metrics and active alerts."""
    poller: AISPoller = app.state.poller
    return poller.get_overview()


@app.get("/api/threats", response_model=List[ThreatAssessment], tags=["Threat Intelligence"])
async def list_threats(
    min_level: Optional[ThreatLevel] = Query(
        None, description="Minimum threat tier to include (NORMAL, ADVISORY, HIGH, CRITICAL)"
    ),
    corridor_only: bool = Query(
        False, description="Filter to only vessels within the 9 NM cable alert horizon"
    ),
):
    """Lists current vessel threat assessments sorted descending by threat score."""
    poller: AISPoller = app.state.poller
    return poller.get_all_assessments(min_level=min_level, only_in_corridor=corridor_only)


@app.get("/api/threats/{mmsi}", response_model=ThreatAssessment, tags=["Threat Intelligence"])
async def get_vessel_threat(mmsi: str):
    """Retrieves current threat assessment and track breakdown for a specific MMSI."""
    poller: AISPoller = app.state.poller
    assessment = poller.get_assessment(mmsi)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with MMSI '{mmsi}' not currently tracked in active memory",
        )
    return assessment


@app.post("/api/evaluate", response_model=ThreatAssessment, tags=["Evaluation & Simulation"])
async def evaluate_vessel(request: EvaluateRequest):
    """Synchronously evaluates threat score for a single vessel telemetry fix.

    Ideal for automated test harnesses, red-team simulation replay, or external webhooks.
    """
    scorer: ThreatScorer = app.state.scorer
    poller: AISPoller = app.state.poller

    # Ingest through poller to update track buffer and dwell cache
    assessment = poller.ingest_vessel_telemetry(
        mmsi=request.mmsi,
        lat=request.lat,
        lon=request.lon,
        sog=request.sog,
        cog=request.cog,
        heading=request.heading,
        name=request.name,
        imo=request.imo,
        ship_type=request.ship_type,
        timestamp_epoch=request.timestamp_epoch,
    )
    return assessment


@app.post("/api/poll", tags=["Telemetry Sync"])
async def trigger_poll():
    """Forces an immediate synchronization cycle against the upstream AIS live feed."""
    poller: AISPoller = app.state.poller
    count = await poller.poll_once()
    return {
        "status": poller._last_poll_status,
        "vessels_ingested": count,
        "total_monitored": len(poller._vessels),
    }


@app.post("/api/alerts/dispatch", response_model=DispatchRecord, tags=["Incident Response"])
async def dispatch_incident_response(request: ManualDispatchRequest):
    """Manually triggers an automated incident response dispatch for a monitored vessel."""
    poller: AISPoller = app.state.poller
    dispatcher: AlertDispatcher = app.state.dispatcher

    threat = poller.get_assessment(request.mmsi)
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with MMSI '{request.mmsi}' is not currently monitored or assessed.",
        )

    record = await dispatcher.dispatch(threat, force=request.force)
    return record


@app.get("/api/alerts/history", response_model=List[DispatchRecord], tags=["Incident Response"])
async def get_dispatch_history(limit: int = Query(50, ge=1, le=500)):
    """Retrieves the recent audit history of executed automated incident response dispatches."""
    dispatcher: AlertDispatcher = app.state.dispatcher
    return dispatcher.get_history(limit=limit)


@app.post("/api/alerts/clear", tags=["Incident Response"])
async def clear_dispatch_history():
    """Clears the incident response audit history and deduplication cooldowns."""
    dispatcher: AlertDispatcher = app.state.dispatcher
    dispatcher.clear_history()
    return {"status": "cleared", "history_count": 0}
