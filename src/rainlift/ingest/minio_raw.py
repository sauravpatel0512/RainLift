"""S3/MinIO helpers for raw zone paths and uploads."""

from __future__ import annotations

import io
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from rainlift.config import Settings, load_settings, s3_endpoint_for_boto


def raw_tlc_key(year: int, month: int, filename: str) -> str:
    return f"raw/tlc/year={year:04d}/month={month:02d}/{filename}"


def raw_weather_key(year: int, month: int, filename: str) -> str:
    return f"raw/weather/year={year:04d}/month={month:02d}/{filename}"


def s3_client(settings: Settings) -> BaseClient:
    cfg = (
        Config(s3={"addressing_style": "path"})
        if settings.s3_path_style
        else Config()
    )
    return boto3.client(
        "s3",
        endpoint_url=s3_endpoint_for_boto(settings),
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name=settings.aws_region,
        config=cfg,
    )


def put_raw_object(
    bucket: str,
    key: str,
    body: bytes | BinaryIO,
    content_type: str | None = None,
    settings: Settings | None = None,
) -> None:
    settings = settings or load_settings()
    client = s3_client(settings)
    extra: dict = {}
    if content_type:
        extra["ContentType"] = content_type
    if isinstance(body, (bytes, bytearray)):
        body = io.BytesIO(body)
    client.upload_fileobj(body, bucket, key, ExtraArgs=extra)
