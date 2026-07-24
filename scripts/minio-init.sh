#!/bin/sh
set -eu
USER="${MINIO_ROOT_USER:-minio}"
PASS="${MINIO_ROOT_PASSWORD:-minio_dev_change_me}"
mc alias set local "http://minio:9000" "$USER" "$PASS"
mc mb --ignore-existing "local/raw"
mc mb --ignore-existing "local/curated"
# Placeholder objects so prefixes exist in UI (S3 has no real folders)
echo "" | mc pipe "local/raw/tlc/.keep"
echo "" | mc pipe "local/raw/weather/.keep"
echo "" | mc pipe "local/curated/.keep"
echo "minio-init: buckets and prefixes ready."