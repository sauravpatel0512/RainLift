"""Run Great Expectations suites against curated Iceberg tables via Trino."""

from __future__ import annotations

import pandas as pd
import trino.dbapi
from great_expectations.dataset import PandasDataset

from rainlift.config import Settings, load_settings
from rainlift.quality.suites import (
    TRIPS_SUITE,
    WEATHER_SUITE,
    apply_suite,
    expectation_count,
    load_suite,
)


def _fetch_all(conn: trino.dbapi.Connection, sql: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description] if cur.description else []
    return pd.DataFrame(rows, columns=cols)


def run_expectations_suite(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
    trips_suite = load_suite(TRIPS_SUITE)
    weather_suite = load_suite(WEATHER_SUITE)

    conn = trino.dbapi.connect(
        host=settings.trino_host,
        port=settings.trino_port,
        user=settings.trino_user,
        catalog="iceberg",
        schema="rainlift",
        http_scheme="http",
    )

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

    print(
        "Great Expectations: OK "
        f"(tlc_trips n={row['n']}, sample={len(df_trips)}, weather={len(df_w)}, "
        f"suite_expectations={expectation_count(trips_suite) + expectation_count(weather_suite)})"
    )
    return None


def main() -> None:
    run_expectations_suite()


if __name__ == "__main__":
    main()
