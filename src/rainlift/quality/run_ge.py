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

    df_trips = _fetch_all(
        conn,
        "SELECT borough, trip_duration_min, year, month FROM iceberg.rainlift.tlc_trips",
    )
    ds_t = PandasDataset(df_trips)
    ds_t.expect_column_values_to_not_be_null("borough")
    ds_t.expect_column_values_to_not_be_null("year")
    res_t = ds_t.validate()
    if not res_t.success:
        raise RuntimeError("Great Expectations failed on curated tlc_trips")

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
    return None


def main() -> None:
    run_expectations_suite()
    print("Great Expectations: OK")


if __name__ == "__main__":
    main()
