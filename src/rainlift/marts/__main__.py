"""CLI: `python -m rainlift.marts` — apply ordered Trino SQL (marts last)."""

from __future__ import annotations

from rainlift.config import load_settings, repo_root
from rainlift.marts.trino_runner import apply_sql_files
from rainlift.quality.run_ge import validate_mart_if_present


def main() -> None:
    settings = load_settings()
    sql_dir = repo_root() / "sql" / "trino"
    apply_sql_files(
        sql_dir=sql_dir,
        host=settings.trino_host,
        port=settings.trino_port,
        user=settings.trino_user,
    )
    print("Applied SQL from", sql_dir)
    validate_mart_if_present(settings)


if __name__ == "__main__":
    main()
