{{ config(materialized='view') }}

with raw_json as (
    select 
        station_id, 
        unnest(results) as record 
    from read_json(
        's3://weather-lake/raw/**/*.json',
        columns={
            'station_id': 'VARCHAR',
            'results': 'STRUCT(date VARCHAR, datatype VARCHAR, value DOUBLE)[]'
        },
        hive_partitioning=true
    )
    where results is not null
)

select
    station_id::varchar as station_id,
    strptime(record.date::varchar, '%Y-%m-%dT%H:%M:%S')::date as observation_date,
    record.datatype::varchar as datatype,
    record.value::numeric as value
from raw_json
