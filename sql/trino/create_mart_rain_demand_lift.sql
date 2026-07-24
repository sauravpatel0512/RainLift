-- Mart: rainy (> 5mm) vs dry (<= 5mm) average demand lift by borough — must be last in apply order.
-- Materialized Iceberg table: Nessie catalogs do not support CREATE VIEW.
DROP TABLE IF EXISTS iceberg.rainlift.rain_demand_lift;

CREATE TABLE iceberg.rainlift.rain_demand_lift AS
WITH classified AS (
  SELECT
    borough,
    trip_date,
    trip_count,
    avg_trip_duration_min,
    CASE WHEN coalesce(precipitation_sum, 0.0) > 5.0 THEN 1 ELSE 0 END AS is_rainy
  FROM iceberg.rainlift.trip_weather_daily
),
agg AS (
  SELECT
    borough,
    avg(CASE WHEN is_rainy = 1 THEN trip_count END) AS rainy_day_avg_trips,
    avg(CASE WHEN is_rainy = 0 THEN trip_count END) AS dry_day_avg_trips,
    avg(CASE WHEN is_rainy = 1 THEN avg_trip_duration_min END) AS rainy_day_avg_duration_min,
    avg(CASE WHEN is_rainy = 0 THEN avg_trip_duration_min END) AS dry_day_avg_duration_min,
    count(CASE WHEN is_rainy = 1 THEN 1 END) AS rainy_days,
    count(CASE WHEN is_rainy = 0 THEN 1 END) AS dry_days
  FROM classified
  GROUP BY borough
)
SELECT
  borough,
  rainy_day_avg_trips,
  dry_day_avg_trips,
  CASE
    WHEN rainy_days = 0 OR dry_days = 0 THEN NULL
    ELSE rainy_day_avg_trips / nullif(dry_day_avg_trips, 0)
  END AS rain_demand_lift,
  rainy_day_avg_duration_min,
  dry_day_avg_duration_min,
  (rainy_days = 0 OR dry_days = 0) AS insufficient_weather_variation
FROM agg
