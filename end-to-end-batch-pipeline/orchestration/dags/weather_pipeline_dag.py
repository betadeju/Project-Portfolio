"""Daily orchestration DAG for the weather pipeline.

Flow: extract (NOAA -> raw storage) -> load raw into warehouse -> dbt build
(staging + marts, including tests) -> data quality checks.

Backfills: `airflow dags backfill weather_pipeline --start-date ... --end-date ...`
works out of the box because extract.py is idempotent per ingestion_date and
dbt models recompute deterministically from bronze history — no special
backfill logic needed beyond Airflow's built-in date range replay.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="weather_pipeline",
    description="Daily NOAA weather ingestion -> dbt star schema",
    default_args=default_args,
    schedule_interval="0 6 * * *",  # 06:00 UTC daily, after NOAA's overnight batch publish
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["weather", "batch", "portfolio"],
) as dag:

    def _extract(**context) -> None:
        from ingestion.extract import run as run_extract

        run_date = context["ds"]  # Airflow execution date, YYYY-MM-DD
        run_extract(datetime.strptime(run_date, "%Y-%m-%d").date())

    extract_task = PythonOperator(
        task_id="extract_noaa_observations",
        python_callable=_extract,
    )

    # Loads new/changed raw partitions from object storage into the
    # warehouse's raw schema. Implemented as a bash step here so it's easy
    # to swap for a bulk COPY/external-table approach at higher volume
    # (see README: "What I'd change at scale").
    load_raw_task = BashOperator(
        task_id="load_raw_to_warehouse",
        bash_command=(
            "python -m ingestion.load_raw --date {{ ds }}"
        ),
    )

    dbt_build_task = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "dbt build --profiles-dir . --target dev "
            "--vars '{\"run_date\": \"{{ ds }}\"}'"
        ),
    )

    dbt_docs_task = BashOperator(
        task_id="dbt_generate_docs",
        bash_command="cd /opt/airflow/dbt && dbt docs generate --profiles-dir . --target dev",
    )

    extract_task >> load_raw_task >> dbt_build_task >> dbt_docs_task
