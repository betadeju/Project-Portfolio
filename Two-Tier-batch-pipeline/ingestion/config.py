"""Centralized configuration for the ingestion layer.

Reads from environment variables so the same code runs locally (docker-compose),
in CI, and in a cloud deployment without changes.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    noaa_api_token: str
    noaa_base_url: str
    station_ids: list[str]
    storage_endpoint: str
    storage_bucket: str
    storage_access_key: str
    storage_secret_key: str
    request_timeout_seconds: int = 30
    max_retries: int = 3


def load_settings() -> Settings:
    """Load settings from environment. Raises if required vars are missing."""
    required = ["NOAA_API_TOKEN", "STORAGE_ENDPOINT", "STORAGE_BUCKET"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {missing}")

    # Example station set (NOAA GHCND station IDs). Swap/extend as needed.
    default_stations = "USW00094728,USW00023174,USW00012960"

    return Settings(
        noaa_api_token=os.environ["NOAA_API_TOKEN"],
        noaa_base_url=os.getenv("NOAA_BASE_URL", "https://www.ncdc.noaa.gov/cdo-web/api/v2"),
        station_ids=os.getenv("NOAA_STATION_IDS", default_stations).split(","),
        storage_endpoint=os.environ["STORAGE_ENDPOINT"],
        storage_bucket=os.environ["STORAGE_BUCKET"],
        storage_access_key=os.getenv("STORAGE_ACCESS_KEY", ""),
        storage_secret_key=os.getenv("STORAGE_SECRET_KEY", ""),
    )
