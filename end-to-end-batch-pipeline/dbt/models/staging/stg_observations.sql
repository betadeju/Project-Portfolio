{#
  Silver layer: cast types, drop obviously invalid readings, and dedupe
  late-arriving revisions by keeping the most recently ingested row per
  (station, date, datatype).

  Idempotency note: NOAA sometimes republishes a corrected value for a
  reading already loaded on a prior run. Because bronze retains every
  ingestion_date's raw file, this model can always recompute "latest known
  value" deterministically from immutable history rather than mutating data
  in place.
#}

with source as (
    select * from {{ source('raw', 'observations') }}
),

typed as (
    select
        station_id,
        cast(observation_date as date)      as observation_date,
        datatype,
        cast(value as numeric)              as reading_value,
        cast(ingestion_date as date)        as ingestion_date
    from source
    where value is not null
),

-- keep only the most recently ingested version of each reading
deduped as (
    select
        *,
        row_number() over (
            partition by station_id, observation_date, datatype
            order by ingestion_date desc
        ) as row_num
    from typed
)

select
    station_id,
    observation_date,
    datatype,
    reading_value,
    ingestion_date
from deduped
where row_num = 1
  -- basic sanity bound; NOAA metric temps are stored in tenths of a degree C
  and not (datatype in ('TMAX', 'TMIN') and abs(reading_value) > 700)
