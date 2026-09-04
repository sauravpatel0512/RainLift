"""CLI: `python -m rainlift.curate` — build curated Iceberg tables and record Mongo runs."""

from __future__ import annotations

import json

from rainlift.config import ingest_date_for_month, load_settings
from rainlift.curate.iceberg_tables import ensure_trips_table, ensure_weather_table
from rainlift.metadata.mongo_runs import ensure_indexes, get_collection, upsert_run


def main() -> None:
    settings = load_settings()
    col = get_collection(settings.mongo_uri, settings.mongo_db)
    ensure_indexes(col)
    ingest_date = ingest_date_for_month(settings.tlc_month)

    n_trips = ensure_trips_table(settings)
    upsert_run(
        col,
        ingest_date,
        "curated_tlc",
        {
            "status": "success",
            "engine": "pyiceberg",
            "row_count": n_trips,
            "content_hash": None,
        },
    )

    n_w = ensure_weather_table(settings)
    upsert_run(
        col,
        ingest_date,
        "curated_weather",
        {
            "status": "success",
            "engine": "pyiceberg",
            "row_count": n_w,
            "content_hash": None,
        },
    )

    print(json.dumps({"ingest_date": ingest_date, "tlc_trips_rows": n_trips, "weather_rows": n_w}, indent=2))


if __name__ == "__main__":
    main()
