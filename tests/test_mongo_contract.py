"""Mongo run document contract (upsert identity + health reads)."""

from __future__ import annotations

from unittest.mock import MagicMock

from rainlift.metadata.mongo_runs import (
    EXPECTED_DATASETS,
    list_runs,
    pipeline_health_summary,
    upsert_run,
)


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


def test_list_runs_queries_with_projection_and_sort() -> None:
    col = MagicMock()
    find_result = MagicMock()
    col.find.return_value = find_result
    find_result.sort.return_value = [{"ingest_date": "2024-01-01", "dataset": "tlc"}]
    got = list_runs(col, ingest_date="2024-01-01")
    col.find.assert_called_once_with({"ingest_date": "2024-01-01"}, {"_id": 0})
    find_result.sort.assert_called_once()
    assert got[0]["dataset"] == "tlc"


def test_pipeline_health_summary_ok_when_all_success() -> None:
    runs = [
        {"ingest_date": "2024-01-01", "dataset": ds, "status": "success", "row_count": 1}
        for ds in sorted(EXPECTED_DATASETS)
    ]
    summary = pipeline_health_summary(runs)
    assert summary["ok"] is True
    assert summary["missing"] == []
    assert summary["failed"] == []
    assert set(summary["success"]) == EXPECTED_DATASETS


def test_pipeline_health_summary_flags_missing_and_failed() -> None:
    runs = [
        {"ingest_date": "2024-01-01", "dataset": "tlc", "status": "success"},
        {"ingest_date": "2024-01-01", "dataset": "weather", "status": "error"},
    ]
    summary = pipeline_health_summary(runs)
    assert summary["ok"] is False
    assert "curated_tlc" in summary["missing"]
    assert "weather" in summary["failed"]
