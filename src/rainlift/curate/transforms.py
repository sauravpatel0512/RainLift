"""Pandas/PyArrow transforms for curated TLC + weather."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import pyarrow as pa
import requests


def load_taxi_zone_lookup(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def trips_parquet_to_frame(parquet_bytes: bytes, zones: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_parquet(io.BytesIO(parquet_bytes))
    zones_small = zones[["LocationID", "Borough"]].drop_duplicates(subset=["LocationID"])
    merged = df.merge(
        zones_small,
        left_on="PULocationID",
        right_on="LocationID",
        how="left",
    )
    merged.rename(columns={"Borough": "borough"}, inplace=True)
    merged["borough"] = merged["borough"].fillna("unknown")

    merged["tpep_pickup_ts"] = pd.to_datetime(merged["tpep_pickup_datetime"])
    merged["tpep_dropoff_ts"] = pd.to_datetime(merged["tpep_dropoff_datetime"])
    delta = (merged["tpep_dropoff_ts"] - merged["tpep_pickup_ts"]).dt.total_seconds() / 60.0
    merged["trip_duration_min"] = delta.where(delta >= 0)

    merged["year"] = merged["tpep_pickup_ts"].dt.year.astype("int32")
    merged["month"] = merged["tpep_pickup_ts"].dt.month.astype("int32")

    out = merged[
        [
            "tpep_pickup_ts",
            "borough",
            "trip_duration_min",
            "year",
            "month",
        ]
    ].copy()
    out = out[out["year"].notna() & out["month"].notna()]
    return out


def open_meteo_json_to_frame(payload: dict[str, Any]) -> pd.DataFrame:
    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    precip = daily.get("precipitation_sum") or []
    temp = daily.get("temperature_2m_mean") or []
    rows = []
    for i, t in enumerate(times):
        rows.append(
            {
                "weather_date": pd.to_datetime(t).normalize(),
                "precipitation_sum": precip[i] if i < len(precip) else None,
                "temperature_2m_mean": temp[i] if i < len(temp) else None,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["year"] = df["weather_date"].dt.year.astype("int32")
        df["month"] = df["weather_date"].dt.month.astype("int32")
    return df


def pandas_to_arrow(df: pd.DataFrame) -> pa.Table:
    return pa.Table.from_pandas(df, preserve_index=False)
