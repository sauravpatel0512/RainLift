"""Apply ordered Trino SQL files (views / marts)."""

from __future__ import annotations

from pathlib import Path


def apply_sql_files(
    *,
    sql_dir: Path,
    order_filename: str = "apply_order.txt",
    host: str,
    port: int,
    user: str,
    catalog: str = "iceberg",
) -> None:
    import trino.dbapi

    order_path = sql_dir / order_filename
    lines = order_path.read_text(encoding="utf-8").splitlines()
    names = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]

    conn = trino.dbapi.connect(
        host=host,
        port=port,
        user=user,
        catalog=catalog,
        http_scheme="http",
    )
    cur = conn.cursor()
    for name in names:
        path = sql_dir / name
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            continue
        cur.execute(sql)
