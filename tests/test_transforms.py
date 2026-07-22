"""Curate transforms."""

import io

import pandas as pd

from rainlift.curate.transforms import open_meteo_json_to_frame, trips_parquet_to_frame


def test_open_meteo_json_to_frame() -> None:
    payload = {
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "precipitation_sum": [0.0, 10.0],
            "temperature_2m_mean": [1.0, 2.0],
        }
    }
    df = open_meteo_json_to_frame(payload)
    assert len(df) == 2
    assert "precipitation_sum" in df.columns


def test_trips_parquet_to_frame_minimal() -> None:
    trips = pd.DataFrame(
        {
            "tpep_pickup_datetime": pd.to_datetime(["2024-01-01 08:00:00"]),
            "tpep_dropoff_datetime": pd.to_datetime(["2024-01-01 08:10:00"]),
            "PULocationID": [1],
        }
    )
    buf = io.BytesIO()
    trips.to_parquet(buf, index=False)
    raw = buf.getvalue()

    zones = pd.DataFrame({"LocationID": [1], "Borough": ["Manhattan"]})
    out = trips_parquet_to_frame(raw, zones)
    assert out.iloc[0]["borough"] == "Manhattan"
    assert out.iloc[0]["month"] == 1
