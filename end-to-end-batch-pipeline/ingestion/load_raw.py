"""Loads raw JSON partitions from object storage into the warehouse's raw
schema, as flat rows ready for dbt's staging models to consume.

Kept deliberately simple (row-by-row insert via a Postgres client) since
this is a portfolio-scale demo. See README "What I'd change at scale" for
the bulk-load approach this would use in production.
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime

import boto3
import psycopg2

from ingestion.config import load_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CREATE_RAW_TABLE_SQL = """
create table if not exists raw.observations (
    station_id text,
    observation_date date,
    datatype text,
    value numeric,
    ingestion_date date
);
"""

UPSERT_SQL = """
delete from raw.observations
where station_id = %(station_id)s and ingestion_date = %(ingestion_date)s;

insert into raw.observations (station_id, observation_date, datatype, value, ingestion_date)
values (%(station_id)s, %(observation_date)s, %(datatype)s, %(value)s, %(ingestion_date)s);
"""


def load_partition_to_warehouse(conn, station_id: str, ingestion_date: date, records: list[dict]) -> int:
    """Idempotently load one station/ingestion_date partition.

    Deletes any existing rows for this exact partition first, so re-running
    a load (e.g. after a backfill) replaces rather than duplicates data.
    """
    count = 0
    with conn.cursor() as cur:
        cur.execute(
            "delete from raw.observations where station_id = %s and ingestion_date = %s",
            (station_id, ingestion_date),
        )
        for record in records:
            cur.execute(
                """
                insert into raw.observations
                    (station_id, observation_date, datatype, value, ingestion_date)
                values (%s, %s, %s, %s, %s)
                """,
                (
                    station_id,
                    record["date"][:10],
                    record["datatype"],
                    record["value"],
                    ingestion_date,
                ),
            )
            count += 1
    conn.commit()
    return count


def run(run_date: date) -> None:
    settings = load_settings()
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
    )
    conn = psycopg2.connect(
        host=settings.__dict__.get("warehouse_host", "warehouse"),
        dbname="weather",
        user="weather_user",
        password="change_me",
    )
    with conn.cursor() as cur:
        cur.execute(CREATE_RAW_TABLE_SQL)
    conn.commit()

    total = 0
    for station_id in settings.station_ids:
        key = f"raw/station_id={station_id}/ingestion_date={run_date.isoformat()}/observations.json"
        obj = s3.get_object(Bucket=settings.storage_bucket, Key=key)
        payload = json.loads(obj["Body"].read())
        records = payload.get("results", [])
        total += load_partition_to_warehouse(conn, station_id, run_date, records)

    logger.info("Loaded %d rows into raw.observations for %s", total, run_date)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(), required=True)
    args = parser.parse_args()
    run(args.date)
