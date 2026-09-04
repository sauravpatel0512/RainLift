"""CLI: `python -m rainlift.ingest` — land TLC + weather to MinIO and record Mongo runs."""

from __future__ import annotations

import json

from rainlift.config import ingest_date_for_month, load_settings
from rainlift.ingest.tlc_fetch import stream_tlc_parquet_to_minio
from rainlift.ingest.weather_fetch import fetch_open_meteo_daily
from rainlift.metadata.mongo_runs import ensure_indexes, get_collection, upsert_run


def main() -> None:
    settings = load_settings()
    col = get_collection(settings.mongo_uri, settings.mongo_db)
    ensure_indexes(col)

    ingest_date = ingest_date_for_month(settings.tlc_month)

    tlc_key, tlc_hash, tlc_bytes = stream_tlc_parquet_to_minio(settings=settings)
    upsert_run(
        col,
        ingest_date,
        "tlc",
        {
            "status": "success",
            "engine": "python",
            "s3_key": tlc_key,
            "content_hash": tlc_hash,
            "row_count": None,
            "extra": {"bytes": tlc_bytes},
        },
    )

    w_key, w_hash, w_bytes = fetch_open_meteo_daily(settings=settings)
    upsert_run(
        col,
        ingest_date,
        "weather",
        {
            "status": "success",
            "engine": "python",
            "s3_key": w_key,
            "content_hash": w_hash,
            "row_count": None,
            "extra": {"bytes": w_bytes},
        },
    )

    print(json.dumps({"ingest_date": ingest_date, "tlc_key": tlc_key, "weather_key": w_key}, indent=2))


if __name__ == "__main__":
    main()
