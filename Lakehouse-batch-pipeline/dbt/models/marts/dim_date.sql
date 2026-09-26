{{ config(materialized='table') }}

with bounds as (
    select
        min(observation_date)::timestamp as min_date,
        max(observation_date)::timestamp as max_date
    from {{ ref('stg_observations') }}
),

spine as (
    select 
        unnest(generate_series(
            min_date, 
            max_date + interval '1 day', 
            interval '1 day'
        ))::date as date_day
    from bounds
    -- Explicitly prevent DuckDB from generating a null sequence
    where min_date is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_key,
    date_day,
    extract(year from date_day)    as year,
    extract(month from date_day)   as month,
    extract(day from date_day)     as day_of_month,
    extract(dow from date_day)     as day_of_week,
    strftime(date_day, '%A')       as day_name,
    strftime(date_day, '%B')       as month_name
from spine
