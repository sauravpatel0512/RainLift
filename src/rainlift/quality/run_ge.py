"""Run Great Expectations suites against curated Iceberg tables via Trino."""

from __future__ import annotations

import pandas as pd
import trino.dbapi
from great_expectations.dataset import PandasDataset

from rainlift.config import Settings, load_settings
from rainlift.quality.suites import (
    MART_LIFT_SUITE,
    TRIPS_SUITE,
    WEATHER_SUITE,
    apply_suite,
    assert_lift_null_when_insufficient,
    expectation_count,
    load_suite,
)


def _fetch_all(conn: trino.dbapi.Connection, sql: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description] if cur.description else []
    return pd.DataFrame(rows, columns=cols)


def _connect(settings: Settings) -> trino.dbapi.Connection:
    return trino.dbapi.connect(
        host=settings.trino_host,
        port=settings.trino_port,
        user=settings.trino_user,
        catalog="iceberg",
        schema="rainlift",
        http_scheme="http",
    )


def validate_mart_if_present(
    settings: Settings | None = None,
    conn: trino.dbapi.Connection | None = None,
) -> str:
    """Apply mart GE suite when ``rain_demand_lift`` exists. Safe to call before marts."""
    settings = settings or load_settings()
    own_conn = conn is None
    conn = conn or _connect(settings)
    try:
        df_mart = _fetch_all(
            conn,
            """
            SELECT
              borough,
              rainy_day_avg_trips,
              dry_day_avg_trips,
              rain_demand_lift,
              insufficient_weather_variation
            FROM iceberg.rainlift.rain_demand_lift
            """,
        )
    except Exception:
        return "skipped (table missing — run make mart)"
    finally:
        if own_conn:
            try:
                conn.close()
            except Exception:
                pass
    if df_mart is None or df_mart.empty:
        return "skipped (empty mart)"
    mart_suite = load_suite(MART_LIFT_SUITE)
    apply_suite(PandasDataset(df_mart), mart_suite)
    ok_lift, lift_detail = assert_lift_null_when_insufficient(df_mart)
    if not ok_lift:
        raise RuntimeError(
            "Mart contract failed: lift must be null when "
            f"insufficient_weather_variation is true ({lift_detail})"
        )
    return f"ok n={len(df_mart)} expectations={expectation_count(mart_suite)}"


def run_expectations_suite(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
    trips_suite = load_suite(TRIPS_SUITE)
    weather_suite = load_suite(WEATHER_SUITE)

    conn = _connect(settings)

    # Full-table null audit (cheap aggregates — avoid pulling multi-million rows into pandas).
    null_trips = _fetch_all(
        conn,
        """
        SELECT
          sum(CASE WHEN borough IS NULL THEN 1 ELSE 0 END) AS null_borough,
          sum(CASE WHEN year IS NULL THEN 1 ELSE 0 END) AS null_year,
          sum(CASE WHEN month IS NULL THEN 1 ELSE 0 END) AS null_month,
          count(*) AS n
        FROM iceberg.rainlift.tlc_trips
        """,
    )
    row = null_trips.iloc[0]
    if (
        int(row["null_borough"] or 0) > 0
        or int(row["null_year"] or 0) > 0
        or int(row["null_month"] or 0) > 0
    ):
        raise RuntimeError(
            f"Great Expectations failed on curated tlc_trips null audit: {null_trips.to_dict()}"
        )

    # Sample for PandasDataset column expectations (portfolio evidence without OOM).
    df_trips = _fetch_all(
        conn,
        """
        SELECT borough, trip_duration_min, year, month
        FROM iceberg.rainlift.tlc_trips
        TABLESAMPLE BERNOULLI (1)
        """,
    )
    if df_trips.empty:
        df_trips = _fetch_all(
            conn,
            "SELECT borough, trip_duration_min, year, month FROM iceberg.rainlift.tlc_trips LIMIT 10000",
        )
    apply_suite(PandasDataset(df_trips), trips_suite)

    df_w = _fetch_all(
        conn,
        "SELECT precipitation_sum, temperature_2m_mean, year, month FROM iceberg.rainlift.weather_daily",
    )
    apply_suite(PandasDataset(df_w), weather_suite)

    mart_msg = validate_mart_if_present(settings, conn=conn)

    print(
        "Great Expectations: OK "
        f"(tlc_trips n={row['n']}, sample={len(df_trips)}, weather={len(df_w)}, "
        f"suite_expectations={expectation_count(trips_suite) + expectation_count(weather_suite)}, "
        f"mart={mart_msg})"
    )
    return None


def main() -> None:
    run_expectations_suite()


if __name__ == "__main__":
    main()
