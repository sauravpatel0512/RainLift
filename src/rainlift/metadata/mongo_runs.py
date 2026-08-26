"""
MongoDB pipeline run documents.

Idempotency: upsert_run keys on (ingest_date, dataset). Re-running ingest for the same
calendar window overwrites the prior document for that dataset instead of appending
unbounded duplicates. Raw object keys in MinIO are also deterministic per month/file.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection

# Datasets written by ingest + curate for one pinned TLC month.
EXPECTED_DATASETS = frozenset({"tlc", "weather", "curated_tlc", "curated_weather"})


def get_collection(uri: str, db_name: str) -> Collection:
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    return client[db_name]["pipeline_runs"]


def ensure_indexes(col: Collection) -> None:
    col.create_index([("ingest_date", ASCENDING), ("dataset", ASCENDING)], unique=True)


def list_runs(
    col: Collection,
    ingest_date: str | None = None,
) -> list[dict[str, Any]]:
    """Return pipeline_runs docs (no `_id`), newest ingest_date first."""
    filt: dict[str, Any] = {}
    if ingest_date:
        filt["ingest_date"] = ingest_date
    cursor = col.find(filt, {"_id": 0}).sort(
        [("ingest_date", DESCENDING), ("dataset", ASCENDING)]
    )
    return list(cursor)


def pipeline_health_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize success coverage for EXPECTED_DATASETS on the latest ingest_date."""
    if not runs:
        return {
            "ingest_date": None,
            "expected": sorted(EXPECTED_DATASETS),
            "present": [],
            "success": [],
            "missing": sorted(EXPECTED_DATASETS),
            "failed": [],
            "ok": False,
        }
    latest = runs[0].get("ingest_date")
    cohort = [r for r in runs if r.get("ingest_date") == latest]
    by_ds = {r.get("dataset"): r for r in cohort if r.get("dataset")}
    present = sorted(by_ds)
    success = sorted(
        ds for ds, r in by_ds.items() if str(r.get("status", "")).lower() == "success"
    )
    failed = sorted(
        ds
        for ds, r in by_ds.items()
        if ds in EXPECTED_DATASETS and str(r.get("status", "")).lower() != "success"
    )
    missing = sorted(EXPECTED_DATASETS - set(by_ds))
    return {
        "ingest_date": latest,
        "expected": sorted(EXPECTED_DATASETS),
        "present": present,
        "success": success,
        "missing": missing,
        "failed": failed,
        "ok": not missing and not failed and set(success) >= EXPECTED_DATASETS,
    }


def upsert_run(
    col: Collection,
    ingest_date: str,
    dataset: str,
    payload: dict[str, Any],
) -> None:
    """
    Upsert by logical identity (ingest_date + dataset).

    `ingest_date` should be the first day of the TLC month as `YYYY-MM-DD`, or a single
    run label consistent across TLC + weather for one ingest pass.
    """
    doc = {
        "ingest_date": ingest_date,
        "dataset": dataset,
        "updated_at": datetime.now(timezone.utc),
        **payload,
    }
    col.update_one(
        {"ingest_date": ingest_date, "dataset": dataset},
        {"$set": doc},
        upsert=True,
    )
