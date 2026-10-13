"""Pydantic data models for Aegis-Sea Threat Engine."""

from typing import Optional
from pydantic import BaseModel, Field


class CableProximity(BaseModel):
    """Result of querying a vessel's position against a submarine cable."""

    cable_id: str = Field(..., description="Unique cable identifier slug (e.g., 'c-lion1')")
    cable_name: str = Field(..., description="Human-readable cable system name")
    color: Optional[str] = Field(None, description="Hex color string for visual display")
    distance_nm: float = Field(..., description="Orthogonal distance to nearest point in Nautical Miles")
    in_cpz: bool = Field(..., description="Whether vessel is within 3 NM Cable Protection Zone")
    in_alert_corridor: bool = Field(..., description="Whether vessel is within 9 NM Alert Corridor")
    s_prox: float = Field(..., description="Normalized spatial proximity score [0.0, 1.0]")
    cable_azimuth_deg: float = Field(..., description="Tangent orientation of closest cable segment [0, 180)")
    nearest_lon: float = Field(..., description="Longitude of closest point on cable")
    nearest_lat: float = Field(..., description="Latitude of closest point on cable")


class CableIndexStats(BaseModel):
    """Statistics for the loaded CableCorridorIndex."""

    total_features: int = Field(..., description="Total GeoJSON feature records (712)")
    total_cables: int = Field(..., description="Unique subsea cable systems (694)")
    total_segments: int = Field(..., description="Total indexed polyline segments (11,989)")
    build_time_ms: float = Field(..., description="R-tree build time in milliseconds")
