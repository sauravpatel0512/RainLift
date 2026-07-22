"""Fetch Open-Meteo daily weather for the TLC month window."""

from __future__ import annotations

import hashlib
import json
from calendar import monthrange
from datetime import date
from typing import Any

import requests

from rainlift.config import Settings, load_settings
from rainlift.ingest.minio_raw import put_raw_object, raw_weather_key


def _month_window(month: str) -> tuple[date, date]:
    y_str, m_str = month.split("-")
    y, m = int(y_str), int(m_str)
    start = date(y, m, 1)
    last = monthrange(y, m)[1]
    end = date(y, m, last)
    return start, end


def fetch_open_meteo_daily(settings: Settings | None = None) -> tuple[str, str, int]:
    """
    Pull daily precipitation + temperature for NYC lat/lon; store JSON in raw zone.

    Returns (s3_key, sha256_hex, byte_length).
    """
    settings = settings or load_settings()
    start, end = _month_window(settings.tlc_month)
    year, month = int(start.year), int(start.month)

    params: dict[str, Any] = {
        "latitude": settings.weather_lat,
        "longitude": settings.weather_lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ["precipitation_sum", "temperature_2m_mean"],
        "timezone": "America/New_York",
    }
    r = requests.get(settings.open_meteo_base_url, params=params, timeout=120)
    r.raise_for_status()
    payload = r.json()
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()

    key = raw_weather_key(year, month, "open_meteo_daily.json")
    put_raw_object(
        settings.raw_bucket,
        key,
        body,
        content_type="application/json",
        settings=settings,
    )
    return key, digest, len(body)
