"""Partition path strings for raw objects."""

from rainlift.ingest.minio_raw import raw_tlc_key, raw_weather_key


def test_raw_tlc_key_layout() -> None:
    assert raw_tlc_key(2024, 1, "yellow_tripdata_2024-01.parquet") == (
        "raw/tlc/year=2024/month=01/yellow_tripdata_2024-01.parquet"
    )


def test_raw_weather_key_layout() -> None:
    assert raw_weather_key(2024, 1, "open_meteo_daily.json") == "raw/weather/year=2024/month=01/open_meteo_daily.json"
