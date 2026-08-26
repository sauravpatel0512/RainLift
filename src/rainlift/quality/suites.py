"""Load Great Expectations JSON suites and apply them to dataframes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

# src/rainlift/quality/suites.py → repo root is parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[3]
CURATED_DIR = (
    _REPO_ROOT / "configs" / "great_expectations" / "expectations" / "curated"
)
MARTS_DIR = (
    _REPO_ROOT / "configs" / "great_expectations" / "expectations" / "marts"
)
RAW_DIR = (
    _REPO_ROOT / "configs" / "great_expectations" / "expectations" / "raw"
)
TRIPS_SUITE = CURATED_DIR / "trips_basic.json"
WEATHER_SUITE = CURATED_DIR / "weather_basic.json"
MART_LIFT_SUITE = MARTS_DIR / "rain_demand_lift.json"
WEATHER_RAW_SUITE = RAW_DIR / "weather_daily_basic.json"

# Expectation types used in curated suites (kept in sync with JSON files).
SUPPORTED_EXPECTATIONS = frozenset(
    {
        "expect_column_values_to_not_be_null",
        "expect_column_values_to_be_between",
        "expect_column_values_to_be_in_set",
        "expect_table_row_count_to_be_between",
    }
)


def load_suite(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def expectation_count(suite: dict[str, Any]) -> int:
    return len(suite.get("expectations") or [])


def assert_suite_supported(suite: dict[str, Any]) -> None:
    for exp in suite.get("expectations") or []:
        name = exp.get("expectation_type")
        if name not in SUPPORTED_EXPECTATIONS:
            raise ValueError(
                f"Unsupported expectation '{name}' in suite "
                f"{suite.get('expectation_suite_name')}"
            )


def evaluate_suite(df: pd.DataFrame, suite: dict[str, Any]) -> tuple[bool, list[str]]:
    """Pure-pandas suite evaluation for CI/offline tests (no GE import required)."""
    assert_suite_supported(suite)
    failures: list[str] = []
    for exp in suite.get("expectations") or []:
        name = exp["expectation_type"]
        kwargs = dict(exp.get("kwargs") or {})
        ok, detail = _eval_one(df, name, kwargs)
        if not ok:
            failures.append(f"{name}: {detail}")
    return (len(failures) == 0), failures


def _eval_one(df: pd.DataFrame, name: str, kwargs: dict[str, Any]) -> tuple[bool, str]:
    if name == "expect_table_row_count_to_be_between":
        n = len(df)
        lo = kwargs.get("min_value")
        hi = kwargs.get("max_value")
        if lo is not None and n < lo:
            return False, f"row_count={n} < min={lo}"
        if hi is not None and n > hi:
            return False, f"row_count={n} > max={hi}"
        return True, "ok"

    col = kwargs["column"]
    series = df[col]
    if name == "expect_column_values_to_not_be_null":
        n_null = int(series.isna().sum())
        return (n_null == 0), f"nulls={n_null}"

    if name == "expect_column_values_to_be_in_set":
        value_set = set(kwargs["value_set"])
        bad = ~series.isna() & ~series.isin(value_set)
        n_bad = int(bad.sum())
        return (n_bad == 0), f"out_of_set={n_bad}"

    if name == "expect_column_values_to_be_between":
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        mostly = float(kwargs.get("mostly", 1.0))
        strict_min = bool(kwargs.get("strict_min", False))
        strict_max = bool(kwargs.get("strict_max", False))
        mask = pd.Series(True, index=series.index)
        if min_value is not None:
            mask &= series > min_value if strict_min else series >= min_value
        if max_value is not None:
            mask &= series < max_value if strict_max else series <= max_value
        # Nulls count as failures for between (GE default behavior for required metrics).
        valid = series.notna()
        compared = valid.sum()
        if compared == 0:
            return False, "no non-null values"
        n_ok = int((mask & valid).sum())
        rate = n_ok / compared
        return (rate >= mostly), f"pass_rate={rate:.4f} mostly={mostly}"

    return False, f"unhandled expectation {name}"


def assert_lift_null_when_insufficient(df: pd.DataFrame) -> tuple[bool, str]:
    """Mart contract: empty rainy or dry cohort → null lift (SQL CASE in create_mart)."""
    if "insufficient_weather_variation" not in df.columns or "rain_demand_lift" not in df.columns:
        return False, "missing insufficient_weather_variation or rain_demand_lift"
    flag = df["insufficient_weather_variation"].fillna(False).astype(bool)
    n_bad = int((flag & df["rain_demand_lift"].notna()).sum())
    return (n_bad == 0), f"lift_present_when_insufficient={n_bad}"


def flatten_open_meteo_daily(payload: dict[str, Any]) -> pd.DataFrame:
    """Flatten Open-Meteo archive JSON (`daily.time` + `daily.precipitation_sum`) for raw GE."""
    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    precip = daily.get("precipitation_sum") or []
    n = min(len(times), len(precip))
    return pd.DataFrame(
        {
            "time": list(times)[:n],
            "precipitation_sum": list(precip)[:n],
        }
    )


def apply_suite(
    dataset: Any,
    suite: dict[str, Any],
    *,
    raise_on_failure: bool = True,
) -> Any:
    """Apply suite via Great Expectations PandasDataset (live Trino path)."""
    from great_expectations.dataset import PandasDataset

    if not isinstance(dataset, PandasDataset):
        dataset = PandasDataset(dataset)

    assert_suite_supported(suite)
    for exp in suite.get("expectations") or []:
        name = exp["expectation_type"]
        kwargs = dict(exp.get("kwargs") or {})
        method = getattr(dataset, name, None)
        if method is None:
            raise AttributeError(
                f"PandasDataset has no expectation method '{name}' "
                f"(suite={suite.get('expectation_suite_name')})"
            )
        method(**kwargs)
    result = dataset.validate()
    if raise_on_failure and not result.success:
        failed = [
            r["expectation_config"]["expectation_type"]
            for r in result.results
            if not r["success"]
        ]
        raise RuntimeError(
            f"Great Expectations suite '{suite.get('expectation_suite_name')}' "
            f"failed: {failed}"
        )
    return result
