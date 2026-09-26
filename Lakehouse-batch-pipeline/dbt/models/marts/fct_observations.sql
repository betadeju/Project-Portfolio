{{ config(
    materialized='external',
    location='s3://weather-lake/gold/fct_observations.parquet'
) }}

with staging as (
    select * from {{ ref('stg_observations') }}
),

date_dim as (
    select * from {{ ref('dim_date') }}
),

station_dim as (
    select * from {{ ref('dim_station') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['staging.station_id', 'staging.observation_date', 'staging.datatype']) }} as observation_key,
    date_dim.date_key,
    station_dim.station_key,
    staging.datatype,
    staging.value
from staging
left join date_dim on staging.observation_date = date_dim.date_day
left join station_dim on staging.station_id = station_dim.station_id
