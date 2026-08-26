"""Streamlit dashboard for `rain_demand_lift` + Mongo pipeline health."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
import trino.dbapi

from rainlift.metadata.mongo_runs import (
    EXPECTED_DATASETS,
    get_collection,
    list_runs,
    pipeline_health_summary,
)


def _render_pipeline_health() -> None:
    st.subheader("Pipeline health")
    st.caption("MongoDB `pipeline_runs` — last status and row counts per dataset.")
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DB", "rainlift")
    try:
        col = get_collection(uri, db_name)
        runs = list_runs(col)
    except Exception as ex:
        st.warning(f"Mongo unreachable — mart data below still works. ({ex})")
        return

    if not runs:
        st.info("No `pipeline_runs` documents yet. Run `make ingest` / `make curate`.")
        return

    summary = pipeline_health_summary(runs)
    ingest_date = summary["ingest_date"]
    cohort = [r for r in runs if r.get("ingest_date") == ingest_date]
    n_ok = len(summary["success"])
    n_expected = len(EXPECTED_DATASETS)

    c1, c2, c3 = st.columns(3)
    c1.metric("Ingest date", str(ingest_date))
    c2.metric("Datasets success", f"{n_ok}/{n_expected}")
    c3.metric("Health", "OK" if summary["ok"] else "Check")

    if summary["missing"]:
        st.error(f"Missing datasets: {', '.join(summary['missing'])}")
    if summary["failed"]:
        st.error(f"Failed datasets: {', '.join(summary['failed'])}")
    if summary["ok"]:
        st.success(f"All {n_expected} expected datasets succeeded for {ingest_date}.")

    view = pd.DataFrame(cohort)
    keep = [c for c in ("dataset", "status", "row_count", "updated_at", "content_hash") if c in view.columns]
    if keep:
        st.dataframe(view[keep], use_container_width=True, hide_index=True)
    else:
        st.dataframe(view, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="RainLift — rain demand lift", layout="wide")
    host = os.environ.get("TRINO_HOST", "localhost")
    port = int(os.environ.get("TRINO_PORT", "8080"))
    user = os.environ.get("TRINO_USER", "rainlift")

    st.title("RainLift — rainy vs dry taxi demand")
    _render_pipeline_health()

    conn = trino.dbapi.connect(
        host=host,
        port=port,
        user=user,
        catalog="iceberg",
        schema="rainlift",
        http_scheme="http",
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM iceberg.rainlift.rain_demand_lift")
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description] if cur.description else []
    df = pd.DataFrame(rows, columns=cols)
    st.subheader("Mart: rain_demand_lift")
    st.caption("Rainy > 5mm vs dry ≤ 5mm daily precipitation.")
    st.dataframe(df, use_container_width=True)
    if not df.empty and "borough" in df.columns:
        chart_df = df.set_index("borough")[["rainy_day_avg_trips", "dry_day_avg_trips"]].fillna(0.0)
        st.bar_chart(chart_df)


if __name__ == "__main__":
    main()
