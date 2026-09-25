-- Minimal sample data so `dbt build` has something to run/test against in CI,
-- without needing real NOAA credentials. Mirrors the shape extract.py produces.

create schema if not exists raw;

create table if not exists raw.observations (
    station_id text,
    observation_date date,
    datatype text,
    value numeric,
    ingestion_date date
);

truncate table raw.observations;

insert into raw.observations (station_id, observation_date, datatype, value, ingestion_date) values
    ('USW00094728', '2024-01-01', 'TMAX', 52,  '2024-01-02'),
    ('USW00094728', '2024-01-01', 'TMIN', -12, '2024-01-02'),
    ('USW00094728', '2024-01-01', 'PRCP', 0,   '2024-01-02'),
    ('USW00094728', '2024-01-02', 'TMAX', 48,  '2024-01-03'),
    ('USW00094728', '2024-01-02', 'TMIN', -20, '2024-01-03'),
    ('USW00023174', '2024-01-01', 'TMAX', 180, '2024-01-02'),
    ('USW00023174', '2024-01-01', 'TMIN', 90,  '2024-01-02'),
    ('USW00023174', '2024-01-01', 'PRCP', 5,   '2024-01-02'),
    -- a duplicate reading with a later ingestion_date, simulating a
    -- late-arriving NOAA revision that stg_observations should dedupe
    ('USW00023174', '2024-01-01', 'TMAX', 182, '2024-01-04');
