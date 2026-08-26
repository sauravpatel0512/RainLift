"""Offline curated suite tests (pure pandas — no Great Expectations import required)."""

from __future__ import annotations

import pandas as pd
import pytest

from rainlift.quality.suites import (
    MART_LIFT_SUITE,
    TRIPS_SUITE,
    WEATHER_RAW_SUITE,
    WEATHER_SUITE,
    assert_lift_null_when_insufficient,
    evaluate_suite,
    expectation_count,
    flatten_open_meteo_daily,
    load_suite,
)


@pytest.fixture
def trips_ok() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "borough": ["Manhattan", "Brooklyn", "Queens"],
            "trip_duration_min": [12.0, 8.5, 20.0],
            "year": [2024, 2024, 2024],
            "month": [1, 1, 1],
        }
    )


@pytest.fixture
def weather_ok() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "precipitation_sum": [0.0] * 20 + [6.2] * 11,
            "temperature_2m_mean": [2.0] * 31,
            "year": [2024] * 31,
            "month": [1] * 31,
        }
    )


def test_suite_files_exist_and_have_expectations():
    trips = load_suite(TRIPS_SUITE)
    weather = load_suite(WEATHER_SUITE)
    mart = load_suite(MART_LIFT_SUITE)
    raw_weather = load_suite(WEATHER_RAW_SUITE)
    assert trips["expectation_suite_name"] == "curated.trips_basic"
    assert weather["expectation_suite_name"] == "curated.weather_basic"
    assert mart["expectation_suite_name"] == "marts.rain_demand_lift"
    assert raw_weather["expectation_suite_name"] == "raw.weather_daily_basic"
    assert expectation_count(trips) >= 6
    assert expectation_count(weather) >= 5
    assert expectation_count(mart) >= 8
    assert expectation_count(raw_weather) >= 4


def test_trips_suite_passes_on_clean_frame(trips_ok):
    ok, failures = evaluate_suite(trips_ok, load_suite(TRIPS_SUITE))
    assert ok, failures


def test_trips_suite_fails_on_null_borough(trips_ok):
    bad = trips_ok.copy()
    bad.loc[0, "borough"] = None
    ok, failures = evaluate_suite(bad, load_suite(TRIPS_SUITE))
    assert not ok
    assert any("not_be_null" in f for f in failures)


def test_trips_suite_fails_on_negative_duration(trips_ok):
    bad = trips_ok.copy()
    bad["trip_duration_min"] = [-5.0, -1.0, -2.0]
    ok, failures = evaluate_suite(bad, load_suite(TRIPS_SUITE))
    assert not ok
    assert any("be_between" in f for f in failures)


def test_weather_suite_passes_on_clean_frame(weather_ok):
    ok, failures = evaluate_suite(weather_ok, load_suite(WEATHER_SUITE))
    assert ok, failures


def test_weather_suite_fails_on_bad_row_count(weather_ok):
    bad = weather_ok.iloc[:5].copy()
    ok, failures = evaluate_suite(bad, load_suite(WEATHER_SUITE))
    assert not ok
    assert any("row_count" in f for f in failures)


def test_weather_suite_fails_on_negative_precip(weather_ok):
    bad = weather_ok.copy()
    bad.loc[0, "precipitation_sum"] = -1.0
    ok, failures = evaluate_suite(bad, load_suite(WEATHER_SUITE))
    assert not ok
    assert any("be_between" in f for f in failures)


@pytest.fixture
def mart_ok() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "borough": ["Manhattan", "Brooklyn", "Queens"],
            "rainy_day_avg_trips": [120.0, 80.0, None],
            "dry_day_avg_trips": [100.0, 90.0, 70.0],
            "rain_demand_lift": [1.2, 80.0 / 90.0, None],
            "insufficient_weather_variation": [False, False, True],
        }
    )


def test_mart_suite_passes_on_clean_frame(mart_ok):
    ok, failures = evaluate_suite(mart_ok, load_suite(MART_LIFT_SUITE))
    assert ok, failures
    flag_ok, detail = assert_lift_null_when_insufficient(mart_ok)
    assert flag_ok, detail


def test_mart_suite_fails_on_unknown_borough(mart_ok):
    bad = mart_ok.copy()
    bad.loc[0, "borough"] = "Atlantis"
    ok, failures = evaluate_suite(bad, load_suite(MART_LIFT_SUITE))
    assert not ok
    assert any("be_in_set" in f for f in failures)


def test_mart_suite_fails_on_negative_lift(mart_ok):
    bad = mart_ok.copy()
    bad.loc[0, "rain_demand_lift"] = -0.1
    ok, failures = evaluate_suite(bad, load_suite(MART_LIFT_SUITE))
    assert not ok
    assert any("be_between" in f for f in failures)


def test_mart_contract_fails_when_lift_set_despite_insufficient(mart_ok):
    bad = mart_ok.copy()
    bad.loc[2, "rain_demand_lift"] = 1.05
    flag_ok, detail = assert_lift_null_when_insufficient(bad)
    assert not flag_ok
    assert "lift_present_when_insufficient=1" in detail


def test_flatten_open_meteo_and_raw_suite_pass():
    payload = {
        "daily": {
            "time": [f"2024-01-{d:02d}" for d in range(1, 32)],
            "precipitation_sum": [0.0] * 20 + [6.0] * 11,
        }
    }
    df = flatten_open_meteo_daily(payload)
    ok, failures = evaluate_suite(df, load_suite(WEATHER_RAW_SUITE))
    assert ok, failures


def test_raw_weather_suite_fails_on_negative_precip():
    payload = {
        "daily": {
            "time": [f"2024-01-{d:02d}" for d in range(1, 32)],
            "precipitation_sum": [-1.0] + [0.0] * 30,
        }
    }
    df = flatten_open_meteo_daily(payload)
    ok, failures = evaluate_suite(df, load_suite(WEATHER_RAW_SUITE))
    assert not ok
    assert any("be_between" in f for f in failures)
