from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="weather_lakehouse_pipeline",
    default_args=default_args,
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    def _extract(**context):
        from ingestion.extract import run as run_extract
        run_extract(datetime.strptime(context["ds"], "%Y-%m-%d").date())

    extract_to_s3 = PythonOperator(
        task_id="extract_noaa_to_bronze",
        python_callable=_extract,
    )

    dbt_build_lakehouse = BashOperator(
        task_id="dbt_build_lakehouse",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "dbt deps && "
            "dbt build --profiles-dir . --target dev"
        ),
    )

    extract_to_s3 >> dbt_build_lakehouse
