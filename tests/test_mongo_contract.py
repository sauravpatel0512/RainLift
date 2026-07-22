"""Mongo run document contract (upsert identity)."""

from __future__ import annotations

from unittest.mock import MagicMock

from rainlift.metadata.mongo_runs import upsert_run


def test_upsert_run_calls_update_one_with_identity_filter() -> None:
    col = MagicMock()
    upsert_run(
        col,
        "2024-01-01",
        "tlc",
        {"status": "success", "content_hash": "abc"},
    )
    col.update_one.assert_called_once()
    args, kwargs = col.update_one.call_args
    assert args[0] == {"ingest_date": "2024-01-01", "dataset": "tlc"}
    assert kwargs.get("upsert") is True
