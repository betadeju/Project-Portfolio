"""Extracts daily weather observations from the NOAA API and lands them
as raw, partitioned JSON in object storage (bronze layer).

Design notes:
- Idempotent: re-running for the same `ingestion_date` overwrites that
  partition's file rather than appending, so retries and backfills are safe.
- Re-checks the last N days on every run to catch NOAA's late-arriving
  revisions to prior readings (see README: "Data quality & idempotency").
- Retries with backoff on transient API failures; fails loudly on repeated
  failure so Airflow can alert rather than silently skipping data.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import time
from datetime import date, datetime, timedelta

import boto3
import requests

from ingestion.config import Settings, load_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LATE_ARRIVAL_LOOKBACK_DAYS = 3


def fetch_observations(settings: Settings, station_id: str, target_date: date) -> dict:
    """Fetch one station's observations for a single date, with retries."""
    url = f"{settings.noaa_base_url}/data"
    params = {
        "datasetid": "GHCND",
        "stationid": station_id,
        "startdate": target_date.isoformat(),
        "enddate": target_date.isoformat(),
        "units": "metric",
        "limit": 1000,
    }
    headers = {"token": settings.noaa_api_token}

    last_error: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            resp = requests.get(
                url, params=params, headers=headers, timeout=settings.request_timeout_seconds
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            wait = 2**attempt
            logger.warning(
                "Fetch failed for station=%s date=%s (attempt %d/%d): %s. Retrying in %ds.",
                station_id, target_date, attempt, settings.max_retries, exc, wait,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"Failed to fetch station={station_id} date={target_date} after "
        f"{settings.max_retries} attempts"
    ) from last_error


def write_raw_partition(settings: Settings, station_id: str, target_date: date, payload: dict) -> str:
    """Write one partition (station + date) to object storage as JSON.

    Overwrites on re-run (idempotent). Partitioned as
    station_id=.../ingestion_date=... so downstream loaders can pick up
    only new/changed partitions.
    """
    key = (
        f"raw/station_id={station_id}/ingestion_date={target_date.isoformat()}/observations.json"
    )
    client = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
    )
    body = io.BytesIO(json.dumps(payload).encode("utf-8"))
    client.upload_fileobj(body, settings.storage_bucket, key)
    logger.info("Wrote partition s3://%s/%s", settings.storage_bucket, key)
    return key


def run(run_date: date) -> list[str]:
    """Extract observations for all configured stations.

    Covers `run_date` plus the last LATE_ARRIVAL_LOOKBACK_DAYS days to catch
    revisions NOAA makes to recently reported readings.
    """
    settings = load_settings()
    written_keys: list[str] = []

    dates_to_process = [
        run_date - timedelta(days=offset)
        for offset in range(LATE_ARRIVAL_LOOKBACK_DAYS + 1)
    ]

    for station_id in settings.station_ids:
        for target_date in dates_to_process:
            payload = fetch_observations(settings, station_id, target_date)
            key = write_raw_partition(settings, station_id, target_date, payload)
            written_keys.append(key)

    logger.info("Extraction complete: %d partitions written", len(written_keys))
    return written_keys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract NOAA weather observations")
    parser.add_argument(
        "--date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        default=date.today(),
        help="Run date in YYYY-MM-DD format (defaults to today, used by Airflow backfills)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(args.date)
