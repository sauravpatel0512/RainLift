-- Borough × calendar day trip aggregates joined to daily weather (fixed month: 2024-01).
CREATE OR REPLACE VIEW iceberg.rainlift.trip_weather_daily AS
WITH trips AS (
  SELECT
    borough,
    CAST(tpep_pickup_ts AS date) AS trip_date,
    count(*) AS trip_count,
    avg(trip_duration_min) AS avg_trip_duration_min
  FROM iceberg.rainlift.tlc_trips
  WHERE year = 2024 AND month = 1
  GROUP BY borough, CAST(tpep_pickup_ts AS date)
),
wx AS (
  SELECT
    CAST(weather_date AS date) AS d,
    precipitation_sum,
    temperature_2m_mean
  FROM iceberg.rainlift.weather_daily
  WHERE year = 2024 AND month = 1
)
SELECT
  t.borough,
  t.trip_date,
  t.trip_count,
  t.avg_trip_duration_min,
  w.precipitation_sum,
  w.temperature_2m_mean
FROM trips t
LEFT JOIN wx w ON t.trip_date = w.d;
