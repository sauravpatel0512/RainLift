"""Stream TLC Parquet from HTTPS into MinIO raw prefix."""

from __future__ import annotations

import hashlib
import tempfile
from typing import Callable

import requests

from rainlift.config import Settings, load_settings
from rainlift.ingest.minio_raw import put_raw_object, raw_tlc_key


def _month_parts(month: str) -> tuple[int, int]:
    y, m = month.split("-")
    return int(y), int(m)


def stream_tlc_parquet_to_minio(
    url: str | None = None,
    settings: Settings | None = None,
    chunk_size: int = 1024 * 1024,
    progress: Callable[[int], None] | None = None,
) -> tuple[str, str, int]:
    """
    Download TLC Parquet via streaming HTTP into MinIO.

    Returns (s3_key, sha256_hex, byte_length).
    """
    settings = settings or load_settings()
    url = url or settings.tlc_parquet_url
    year, month = _month_parts(settings.tlc_month)
    filename = url.rstrip("/").split("/")[-1]
    key = raw_tlc_key(year, month, filename)

    h = hashlib.sha256()
    total = 0
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with tempfile.SpooledTemporaryFile(max_size=256 * 1024 * 1024) as tmp:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                h.update(chunk)
                total += len(chunk)
                tmp.write(chunk)
                if progress:
                    progress(total)
            tmp.seek(0)
            put_raw_object(
                settings.raw_bucket,
                key,
                tmp,
                content_type="application/vnd.apache.parquet",
                settings=settings,
            )
    return key, h.hexdigest(), total
