"""
MongoDB pipeline run documents.

Idempotency: upsert_run keys on (ingest_date, dataset). Re-running ingest for the same
calendar window overwrites the prior document for that dataset instead of appending
unbounded duplicates. Raw object keys in MinIO are also deterministic per month/file.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection


def get_collection(uri: str, db_name: str) -> Collection:
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    return client[db_name]["pipeline_runs"]


def ensure_indexes(col: Collection) -> None:
    col.create_index([("ingest_date", ASCENDING), ("dataset", ASCENDING)], unique=True)


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
