{#
  Station dimension. Currently derived from distinct stations seen in
  observations; in production this would join a proper NOAA stations
  metadata feed for name/lat/lon/elevation instead of inferring from
  reading history alone.
#}

with stations as (
    select distinct station_id
    from {{ ref('stg_observations') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['station_id']) }} as station_key,
    station_id
from stations
