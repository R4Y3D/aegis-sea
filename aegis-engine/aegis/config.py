"""Aegis-Sea Configuration and Parameters."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Aegis-Sea Threat Engine."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8400
    debug: bool = False

    # Upstream Node.js feed settings
    node_server_url: str = "http://127.0.0.1:4173"
    poll_interval_seconds: float = 30.0

    # Geospatial thresholds (Nautical Miles)
    alert_horizon_nm: float = 9.0      # Maximum corridor evaluation horizon (d_max)
    cpz_radius_nm: float = 3.0         # Cable Protection Zone radius (critical zone)

    # Composite Threat Weights (Sum = 100)
    weight_proximity: float = 30.0     # w_p: Spatial Proximity
    weight_speed: float = 20.0         # w_s: Kinematic Speed Anomaly
    weight_loiter: float = 20.0        # w_l: Loitering & Dwell Time
    weight_heading: float = 10.0       # w_h: Course Heading Alignment
    weight_anchor: float = 10.0        # w_a: Historical Anchor-Dragging Signature
    weight_dark: float = 10.0          # w_d: AIS Transmission Continuity (Dark Ship)

    # Speed factor parameters
    speed_midpoint_knots: float = 4.0  # v_mid: Logistic midpoint velocity
    speed_steepness: float = 1.2       # k_s: Logistic steepness

    # Threat Tier Thresholds
    threshold_critical: float = 75.0   # T >= 75
    threshold_warning: float = 50.0    # 50 <= T < 75
    threshold_advisory: float = 25.0   # 25 <= T < 50

    # Submarine cable GeoJSON path
    cable_geojson_path: Path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "data"
        / "local_data"
        / "telegeography_submarine_cables"
        / "cable-geo.json"
    )

    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
