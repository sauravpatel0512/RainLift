"""Streamlit dashboard for `rain_demand_lift`."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
import trino.dbapi


def main() -> None:
    st.set_page_config(page_title="RainLift — rain demand lift", layout="wide")
    host = os.environ.get("TRINO_HOST", "localhost")
    port = int(os.environ.get("TRINO_PORT", "8080"))
    user = os.environ.get("TRINO_USER", "rainlift")

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
    st.title("RainLift — rainy vs dry taxi demand")
    st.caption("Mart: `rain_demand_lift` (rainy > 5mm vs dry ≤ 5mm daily precipitation).")
    st.dataframe(df, use_container_width=True)
    chart_df = df.set_index("borough")[["rainy_day_avg_trips", "dry_day_avg_trips"]].fillna(0.0)
    st.bar_chart(chart_df)


if __name__ == "__main__":
    main()
