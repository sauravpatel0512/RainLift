"""Create or refresh curated Iceberg tables via Nessie + MinIO."""

from __future__ import annotations

import json
from typing import Any

from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError

from rainlift.config import Settings, load_settings, s3_endpoint_for_boto
from rainlift.curate import transforms
from rainlift.ingest.minio_raw import raw_tlc_key, raw_weather_key, s3_client


def _catalog(settings: Settings) -> Any:
    # PyIceberg 0.7 has no native Nessie type — use Nessie Iceberg REST.
    # Host URI uses localhost; Compose pipeline overrides NESSIE_URI to nessie:19120/api/v1,
    # so derive the Iceberg REST base from that host.
    nessie_base = settings.nessie_uri.rstrip("/")
    for suffix in ("/api/v2", "/api/v1", "/api"):
        if nessie_base.endswith(suffix):
            nessie_base = nessie_base[: -len(suffix)]
            break
    rest_uri = f"{nessie_base}/iceberg"
    return load_catalog(
        "rainlift",
        **{
            "type": "rest",
            "uri": rest_uri,
            "warehouse": settings.iceberg_warehouse.rstrip("/"),
            "s3.endpoint": s3_endpoint_for_boto(settings),
            "s3.access-key-id": settings.minio_access_key,
            "s3.secret-access-key": settings.minio_secret_key,
            "s3.path-style-access": "true",
            "s3.region": settings.aws_region,
            "downcast-ns-timestamp-to-us-on-write": "true",
        },
    )


def _ensure_ns(cat: Any, ns: str) -> None:
    try:
        cat.create_namespace(ns)
    except Exception:  # noqa: BLE001
        pass


def _read_raw_bytes(settings: Settings, key: str) -> bytes:
    client = s3_client(settings)
    obj = client.get_object(Bucket=settings.raw_bucket, Key=key)
    return obj["Body"].read()


def _overwrite_table(cat: Any, ident: tuple[str, str], arrow_tbl: Any) -> None:
    try:
        cat.load_table(ident)
    except NoSuchTableError:
        cat.create_table(ident, schema=arrow_tbl.schema)
    cat.load_table(ident).overwrite(arrow_tbl)


def ensure_trips_table(settings: Settings | None = None) -> int:
    settings = settings or load_settings()
    y, m = map(int, settings.tlc_month.split("-"))
    fname = settings.tlc_parquet_url.rstrip("/").split("/")[-1]
    key = raw_tlc_key(y, m, fname)
    zones = transforms.load_taxi_zone_lookup(settings.taxi_zone_lookup_url)
    raw = _read_raw_bytes(settings, key)
    df = transforms.trips_parquet_to_frame(raw, zones)
    arrow_tbl = transforms.pandas_to_arrow(df)

    cat = _catalog(settings)
    _ensure_ns(cat, "rainlift")
    _overwrite_table(cat, ("rainlift", "tlc_trips"), arrow_tbl)
    return len(df)


def ensure_weather_table(settings: Settings | None = None) -> int:
    settings = settings or load_settings()
    y, m = map(int, settings.tlc_month.split("-"))
    key = raw_weather_key(y, m, "open_meteo_daily.json")
    raw = _read_raw_bytes(settings, key)
    payload = json.loads(raw.decode("utf-8"))
    df = transforms.open_meteo_json_to_frame(payload)
    arrow_tbl = transforms.pandas_to_arrow(df)

    cat = _catalog(settings)
    _ensure_ns(cat, "rainlift")
    _overwrite_table(cat, ("rainlift", "weather_daily"), arrow_tbl)
    return len(df)
