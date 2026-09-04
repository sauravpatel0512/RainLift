"""Load settings from environment (optional `.env` for local dev)."""

from __future__ import annotations

import os
from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def repo_root() -> Path:
    """Repository root (`RainLift/config.py` lives in `src/rainlift/`)."""
    return Path(__file__).resolve().parents[2]


def parse_tlc_month(ym: str) -> tuple[int, int]:
    """Parse pinned ``YYYY-MM`` into ``(year, month)``."""
    y, m = ym.split("-")
    return int(y), int(m)


def ingest_date_for_month(ym: str) -> str:
    """First calendar day of TLC month as ``YYYY-MM-DD`` (Mongo run identity)."""
    y, m = parse_tlc_month(ym)
    return date(y, m, 1).isoformat()


def month_window(ym: str) -> tuple[date, date]:
    """Inclusive start/end dates for the pinned TLC month."""
    y, m = parse_tlc_month(ym)
    return date(y, m, 1), date(y, m, monthrange(y, m)[1])


@dataclass(frozen=True)
class Settings:
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    raw_bucket: str
    curated_bucket: str
    nessie_uri: str
    iceberg_warehouse: str
    mongo_uri: str
    mongo_db: str
    trino_host: str
    trino_port: int
    trino_user: str
    tlc_month: str
    tlc_parquet_url: str
    taxi_zone_lookup_url: str
    open_meteo_base_url: str
    weather_lat: float
    weather_lon: float
    aws_region: str
    s3_path_style: bool


def _bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    env_path = repo_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path)

    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
    access = os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("MINIO_ROOT_USER", "minio")
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY") or os.environ.get("MINIO_ROOT_PASSWORD", "minio_dev_change_me")

    tlc_month = os.environ.get("TLC_MONTH", "2024-01")
    if len(tlc_month) != 7 or tlc_month[4] != "-":
        raise ValueError("TLC_MONTH must be YYYY-MM")

    return Settings(
        minio_endpoint=minio_endpoint.rstrip("/"),
        minio_access_key=access,
        minio_secret_key=secret,
        raw_bucket=os.environ.get("RAW_BUCKET", "raw"),
        curated_bucket=os.environ.get("CURATED_BUCKET", "curated"),
        # Nessie REST root; PyIceberg + Trino both talk to the same server (v1/v2 paths vary by client).
        nessie_uri=os.environ.get("NESSIE_URI", "http://localhost:19120/api/v1").rstrip("/"),
        iceberg_warehouse=os.environ.get("ICEBERG_WAREHOUSE", "s3://curated/wh/").rstrip("/") + "/",
        mongo_uri=os.environ.get("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db=os.environ.get("MONGO_DB", "rainlift"),
        trino_host=os.environ.get("TRINO_HOST", "localhost"),
        trino_port=int(os.environ.get("TRINO_PORT", "8080")),
        trino_user=os.environ.get("TRINO_USER", "rainlift"),
        tlc_month=tlc_month,
        tlc_parquet_url=os.environ.get(
            "TLC_PARQUET_URL",
            "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
        ),
        taxi_zone_lookup_url=os.environ.get(
            "TAXI_ZONE_LOOKUP_URL",
            "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv",
        ),
        open_meteo_base_url=os.environ.get(
            "OPEN_METEO_BASE_URL",
            "https://archive-api.open-meteo.com/v1/archive",
        ).rstrip("/"),
        weather_lat=float(os.environ.get("WEATHER_LAT", "40.7128")),
        weather_lon=float(os.environ.get("WEATHER_LON", "-74.006")),
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        s3_path_style=_bool(os.environ.get("S3_PATH_STYLE_ACCESS"), True),
    )


def s3_endpoint_for_boto(settings: Settings) -> str:
    """boto3 `endpoint_url` from MINIO_ENDPOINT (no trailing path)."""
    u = urlparse(settings.minio_endpoint)
    if not u.scheme or not u.netloc:
        raise ValueError(f"Invalid MINIO_ENDPOINT: {settings.minio_endpoint!r}")
    return f"{u.scheme}://{u.netloc}"
