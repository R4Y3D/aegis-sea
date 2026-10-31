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

    # Composite Threat Weights (Sum = 100.0)
    weight_proximity: float = 30.0     # w_p: Spatial Proximity (quadratic decay)
    weight_speed: float = 20.0         # w_s: Kinematic Speed Anomaly (sigmoid)
    weight_loiter: float = 20.0        # w_l: Loitering & Dwell Time
    weight_heading: float = 10.0       # w_h: Course Heading Alignment
    weight_anchor: float = 10.0        # w_a: Anchor Drag Deceleration Catch Signature
    weight_dark: float = 10.0          # w_d: AIS Transmission Blackout / Silence

    # Speed factor parameters (Sigmoid logistic)
    speed_midpoint_knots: float = 4.0  # v_mid: Logistic inflection velocity
    speed_steepness: float = 1.2       # k_s: Logistic steepness

    # Dwell & Blackout Horizons (Seconds)
    loiter_tau_seconds: float = 3600.0  # tau_loiter: 60 minutes
    dark_tau_seconds: float = 1800.0    # tau_dark: 30 minutes

    # Anchor Catch Signature Window
    anchor_decel_window_seconds: float = 600.0  # 10 minutes
    anchor_prior_speed_min: float = 6.0         # Previous speed above 6.0 kn
    anchor_current_speed_max: float = 1.5       # Current speed at or below 1.5 kn

    # Telemetry Trust Layer (Jump filter against spoofing)
    max_plausible_vessel_speed_knots: float = 35.0  # Commercial ship displacement hull limit
    ghost_track_min_samples: int = 3                 # Require at least 3 historical points before failover

    # Operational Threat Tier Thresholds (0 to 100)
    threshold_critical: float = 81.0   # T >= 81: Imminent Cut / Pre-emptive Failover
    threshold_high: float = 61.0       # 61 <= T < 81: Active Threat / SOAR Webhook
    threshold_advisory: float = 31.0   # 31 <= T < 61: Advisory Watch / Increased Polling

    # Incident Response & SOAR Dispatcher Settings
    soar_webhook_url: str | None = None
    bgp_controller_webhook_url: str | None = None
    alert_cooldown_seconds: float = 300.0  # 5 minutes deduplication cooldown
    auto_dispatch_enabled: bool = True     # Auto-dispatch on live poller HIGH/CRITICAL threats

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
