{#
  Fact table, grain: one row per station per date per reading type.
  Pivoted wide (tmax/tmin/precip as columns) since that's the most common
  analytics access pattern for weather data; a long/narrow version is
  trivial to derive from stg_observations directly if needed.
#}

with obs as (
    select * from {{ ref('stg_observations') }}
),

pivoted as (
    select
        station_id,
        observation_date,
        max(case when datatype = 'TMAX' then reading_value end) as temp_max_c,
        max(case when datatype = 'TMIN' then reading_value end) as temp_min_c,
        max(case when datatype = 'PRCP' then reading_value end) as precipitation_mm,
        max(case when datatype = 'SNOW' then reading_value end) as snowfall_mm
    from obs
    group by station_id, observation_date
)

select
    {{ dbt_utils.generate_surrogate_key(['p.station_id', 'p.observation_date']) }} as observation_key,
    ds.station_key,
    dd.date_key,
    p.station_id,
    p.observation_date,
    p.temp_max_c,
    p.temp_min_c,
    p.precipitation_mm,
    p.snowfall_mm
from pivoted p
left join {{ ref('dim_station') }} ds on p.station_id = ds.station_id
left join {{ ref('dim_date') }} dd on p.observation_date = dd.date_day
