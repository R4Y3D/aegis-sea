"""Two-tier Spatial Index over Submarine Cable Geometries.

Tier 1: Bounding-box R-tree spatial indexing for O(log M) candidate pruning.
Tier 2: Local Cartesian projection and Shapely exact orthogonal distance d(v, c).
"""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from rtree import index
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

from aegis.config import settings
from aegis.models import CableIndexStats, CableProximity

logger = logging.getLogger(__name__)


class CableSegment:
    """Internal lightweight representation of a single cable line segment."""

    __slots__ = ("cable_id", "cable_name", "color", "p1", "p2")

    def __init__(
        self,
        cable_id: str,
        cable_name: str,
        color: Optional[str],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
    ) -> None:
        self.cable_id = cable_id
        self.cable_name = cable_name
        self.color = color
        self.p1 = p1  # (lon, lat)
        self.p2 = p2  # (lon, lat)


class CableCorridorIndex:
    """Two-tier spatial index indexing 712 submarine cables for real-time vessel threat evaluation."""

    def __init__(self, geojson_path: Optional[Union[str, Path]] = None, auto_load: bool = True) -> None:
        self.geojson_path = Path(geojson_path or settings.cable_geojson_path)
        self._rtree: Optional[index.Index] = None
        self._segments: List[CableSegment] = []
        self._cable_metadata: Dict[str, Dict[str, Any]] = {}
        self._total_features: int = 0
        self._build_time_ms: float = 0.0

        if auto_load:
            self.load_geojson(self.geojson_path)

    @property
    def total_features(self) -> int:
        """Total number of GeoJSON feature records in the dataset (712)."""
        return self._total_features

    @property
    def total_cables(self) -> int:
        """Total number of unique submarine cable systems loaded (694)."""
        return len(self._cable_metadata)

    @property
    def total_segments(self) -> int:
        """Total number of indexed polyline segments in the R-tree (11,989)."""
        return len(self._segments)

    def get_stats(self) -> CableIndexStats:
        """Return operational statistics for the spatial index."""
        return CableIndexStats(
            total_features=self.total_features,
            total_cables=self.total_cables,
            total_segments=self.total_segments,
            build_time_ms=round(self._build_time_ms, 2),
        )

    def load_geojson(self, path: Union[str, Path]) -> None:
        """Load TeleGeography cable-geo.json and construct the two-tier R-tree index."""
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Submarine cable GeoJSON not found at: {target_path}")

        t_start = time.perf_counter()

        with open(target_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        features = geojson_data.get("features", [])
        if not features:
            raise ValueError(f"No features found in GeoJSON: {target_path}")

        # Initialize fresh in-memory R-tree and data containers
        rtree_idx = index.Index()
        segments: List[CableSegment] = []
        cables_meta: Dict[str, Dict[str, Any]] = {}
        seg_id = 0

        for feat in features:
            props = feat.get("properties", {})
            cable_id = props.get("id") or f"cable-{seg_id}"
            cable_name = props.get("name", "Unknown Subsea Cable")
            color = props.get("color")

            if cable_id not in cables_meta:
                cables_meta[cable_id] = {
                    "id": cable_id,
                    "name": cable_name,
                    "color": color,
                    "segment_count": 0,
                }

            geometry = feat.get("geometry", {})
            geom_type = geometry.get("type")
            coords_data = geometry.get("coordinates", [])

            # Handle MultiLineString and LineString geometries
            lines: List[List[List[float]]] = []
            if geom_type == "MultiLineString":
                lines = coords_data
            elif geom_type == "LineString":
                lines = [coords_data]

            for line in lines:
                for i in range(len(line) - 1):
                    p1 = (float(line[i][0]), float(line[i][1]))
                    p2 = (float(line[i + 1][0]), float(line[i + 1][1]))

                    # Calculate segment bounding envelope (min_lon, min_lat, max_lon, max_lat)
                    min_lon = min(p1[0], p2[0])
                    max_lon = max(p1[0], p2[0])
                    min_lat = min(p1[1], p2[1])
                    max_lat = max(p1[1], p2[1])

                    seg = CableSegment(
                        cable_id=cable_id,
                        cable_name=cable_name,
                        color=color,
                        p1=p1,
                        p2=p2,
                    )
                    segments.append(seg)
                    rtree_idx.insert(seg_id, (min_lon, min_lat, max_lon, max_lat))

                    seg_id += 1
                    cables_meta[cable_id]["segment_count"] += 1

        self._rtree = rtree_idx
        self._segments = segments
        self._cable_metadata = cables_meta
        self._total_features = len(features)
        self._build_time_ms = (time.perf_counter() - t_start) * 1000.0

        logger.info(
            "Constructed CableCorridorIndex: %d features, %d unique cables, %d segments in %.2f ms",
            self.total_features,
            self.total_cables,
            self.total_segments,
            self._build_time_ms,
        )

    def query_corridor(
        self,
        lat: float,
        lon: float,
        max_distance_nm: float = settings.alert_horizon_nm,
    ) -> List[CableProximity]:
        """Query for all cables within max_distance_nm of the vessel position.

        Args:
            lat: Vessel latitude in WGS84 decimal degrees [-90.0, 90.0].
            lon: Vessel longitude in WGS84 decimal degrees [-180.0, 180.0].
            max_distance_nm: Maximum radial evaluation distance in Nautical Miles. Defaults to 9.0 NM.

        Returns:
            List of CableProximity objects sorted in ascending order of orthogonal distance.
        """
        if self._rtree is None:
            raise RuntimeError("CableCorridorIndex has not been initialized.")

        # Coordinate bounds safety clamping
        lat = max(-89.9, min(89.9, lat))
        cos_lat = max(0.001, math.cos(math.radians(lat)))

        # Tier 1: Determine bounding box in degrees (1 NM = 1/60 deg latitude)
        d_lat = max_distance_nm / 60.0
        d_lon = d_lat / cos_lat

        # Candidate segment IDs from Tier 1 R-tree
        candidate_ids: List[int] = []

        # Antimeridian wrap-around handling
        if lon - d_lon < -180.0:
            # Query left side (-180 to lon + d_lon) and wrapped right side
            box1 = (-180.0, lat - d_lat, lon + d_lon, lat + d_lat)
            box2 = (lon - d_lon + 360.0, lat - d_lat, 180.0, lat + d_lat)
            candidate_ids.extend(self._rtree.intersection(box1))
            candidate_ids.extend(self._rtree.intersection(box2))
        elif lon + d_lon > 180.0:
            # Query right side (lon - d_lon to 180) and wrapped left side
            box1 = (lon - d_lon, lat - d_lat, 180.0, lat + d_lat)
            box2 = (-180.0, lat - d_lat, lon + d_lon - 360.0, lat + d_lat)
            candidate_ids.extend(self._rtree.intersection(box1))
            candidate_ids.extend(self._rtree.intersection(box2))
        else:
            q_box = (lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat)
            candidate_ids.extend(self._rtree.intersection(q_box))

        if not candidate_ids:
            return []

        # Group candidate segments by cable_id
        by_cable: Dict[str, List[CableSegment]] = {}
        for cid in candidate_ids:
            seg = self._segments[cid]
            by_cable.setdefault(seg.cable_id, []).append(seg)

        results: List[CableProximity] = []
        vessel_pt = Point(0.0, 0.0)

        # Tier 2: Exact orthogonal projection & distance computation
        for cable_id, seg_list in by_cable.items():
            cable_name = seg_list[0].cable_name
            color = seg_list[0].color

            min_dist = float("inf")
            closest_seg_data: Optional[Tuple[CableSegment, Tuple[float, float], Tuple[float, float]]] = None
            closest_pt_on_geom: Optional[Point] = None

            for s in seg_list:
                # Delta lon with antimeridian wrapping
                dlon1 = s.p1[0] - lon
                if dlon1 > 180.0:
                    dlon1 -= 360.0
                elif dlon1 < -180.0:
                    dlon1 += 360.0

                dlon2 = s.p2[0] - lon
                if dlon2 > 180.0:
                    dlon2 -= 360.0
                elif dlon2 < -180.0:
                    dlon2 += 360.0

                # Convert to local Cartesian frame in Nautical Miles
                x1 = dlon1 * cos_lat * 60.0
                y1 = (s.p1[1] - lat) * 60.0
                x2 = dlon2 * cos_lat * 60.0
                y2 = (s.p2[1] - lat) * 60.0

                seg_geom = LineString([(x1, y1), (x2, y2)])
                dist = vessel_pt.distance(seg_geom)

                if dist < min_dist:
                    min_dist = dist
                    closest_seg_data = (s, (x1, y1), (x2, y2))
                    _, nearest = nearest_points(vessel_pt, seg_geom)
                    closest_pt_on_geom = nearest

            if min_dist <= max_distance_nm and closest_seg_data is not None and closest_pt_on_geom is not None:
                _, (x1, y1), (x2, y2) = closest_seg_data
                dx = x2 - x1
                dy = y2 - y1

                # Tangent orientation in degrees relative to True North [0.0, 180.0)
                seg_azimuth = (math.degrees(math.atan2(dx, dy))) % 180.0

                # Quadratic spatial proximity score S_prox in [0.0, 1.0]
                s_prox = max(0.0, 1.0 - (min_dist / max_distance_nm)) ** 2

                # Convert local coordinates back to WGS84 coordinates for closest point
                nearest_lon = lon + (closest_pt_on_geom.x / (cos_lat * 60.0))
                # Wrap lon back into [-180, 180]
                if nearest_lon > 180.0:
                    nearest_lon -= 360.0
                elif nearest_lon < -180.0:
                    nearest_lon += 360.0

                nearest_lat = lat + (closest_pt_on_geom.y / 60.0)

                results.append(
                    CableProximity(
                        cable_id=cable_id,
                        cable_name=cable_name,
                        color=color,
                        distance_nm=round(min_dist, 4),
                        in_cpz=(min_dist <= settings.cpz_radius_nm),
                        in_alert_corridor=True,
                        s_prox=round(s_prox, 4),
                        cable_azimuth_deg=round(seg_azimuth, 2),
                        nearest_lon=round(nearest_lon, 6),
                        nearest_lat=round(nearest_lat, 6),
                    )
                )

        results.sort(key=lambda r: r.distance_nm)
        return results

    def get_closest_cable(
        self,
        lat: float,
        lon: float,
        max_distance_nm: float = settings.alert_horizon_nm,
    ) -> Optional[CableProximity]:
        """Convenience method returning the single closest cable, or None if none within horizon."""
        results = self.query_corridor(lat, lon, max_distance_nm=max_distance_nm)
        return results[0] if results else None

    def is_in_corridor(
        self,
        lat: float,
        lon: float,
        max_distance_nm: float = settings.alert_horizon_nm,
    ) -> bool:
        """Fast boolean check whether a vessel is within the alert corridor of any cable."""
        results = self.query_corridor(lat, lon, max_distance_nm=max_distance_nm)
        return len(results) > 0
