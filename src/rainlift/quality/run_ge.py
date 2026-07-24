"""Run Great Expectations suites against curated Iceberg tables via Trino."""

from __future__ import annotations

import pandas as pd
import trino.dbapi
from great_expectations.dataset import PandasDataset

from rainlift.config import Settings, load_settings, repo_root


def _fetch_all(conn: trino.dbapi.Connection, sql: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description] if cur.description else []
    return pd.DataFrame(rows, columns=cols)


def run_expectations_suite(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
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
          count(*) AS n
        FROM iceberg.rainlift.tlc_trips
        """,
    )
    if int(null_trips.iloc[0]["null_borough"] or 0) > 0 or int(null_trips.iloc[0]["null_year"] or 0) > 0:
        raise RuntimeError(f"Great Expectations failed on curated tlc_trips null audit: {null_trips.to_dict()}")

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
    ds_t = PandasDataset(df_trips)
    ds_t.expect_column_values_to_not_be_null("borough")
    ds_t.expect_column_values_to_not_be_null("year")
    res_t = ds_t.validate()
    if not res_t.success:
        raise RuntimeError("Great Expectations failed on curated tlc_trips sample")

    df_w = _fetch_all(
        conn,
        "SELECT precipitation_sum, temperature_2m_mean, year, month FROM iceberg.rainlift.weather_daily",
    )
    ds_w = PandasDataset(df_w)
    ds_w.expect_column_values_to_not_be_null("year")
    res_w = ds_w.validate()
    if not res_w.success:
        raise RuntimeError("Great Expectations failed on curated weather_daily")

    _ = repo_root()  # reserved for future great.yml wiring
    print(f"Great Expectations: OK (tlc_trips n={null_trips.iloc[0]['n']}, sample={len(df_trips)}, weather={len(df_w)})")
    return None


def main() -> None:
    run_expectations_suite()


if __name__ == "__main__":
    main()
