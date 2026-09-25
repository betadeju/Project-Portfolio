{#
  Standard date dimension, spun off the observed date range in the data
  rather than a fixed calendar spine, so it grows automatically as new
  dates are ingested.
#}

with bounds as (
    select
        min(observation_date) as min_date,
        max(observation_date) as max_date
    from {{ ref('stg_observations') }}
),

spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="(select min_date from bounds)",
        end_date="(select max_date + interval '1 day' from bounds)"
    ) }}
)

select
    {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_key,
    date_day,
    extract(year from date_day)    as year,
    extract(month from date_day)   as month,
    extract(day from date_day)     as day_of_month,
    extract(dow from date_day)     as day_of_week,
    to_char(date_day, 'Day')       as day_name,
    to_char(date_day, 'Month')     as month_name
from spine
