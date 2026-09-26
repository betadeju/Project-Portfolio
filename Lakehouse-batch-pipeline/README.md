# Modern Data Stack
# Weather Data Pipeline (Two-Tier (Data Lake + Data Warehouse) architecture)

An end-to-end batch pipeline that ingests daily weather observations from the NOAA API, lands them in a raw storage layer, models them through a bronze → silver → gold architecture with dbt, and surfaces analytics-ready tables in a warehouse — with idempotent backfills, data quality tests, and CI on every PR.

> Swap the source: this repo is structured so the ingestion layer is decoupled from modeling. Point `ingestion/extract.py` at a different API (transit, market data, etc.) and the dbt layer, orchestration, and tests carry over unchanged.

## Architecture

flowchart LR
    A[NOAA API] -->|Python extract| B[Bronze: raw JSON in Garage S3]
    B -->|dbt + DuckDB read| C(In-Memory Compute)
    C -->|dbt + DuckDB write| D[Silver: Parquet in Garage S3]
    C -->|dbt + DuckDB write| E[Gold: Parquet in Garage S3]
    
    F[Airflow DAG] -.orchestrates.-> A
    F -.orchestrates.-> C

