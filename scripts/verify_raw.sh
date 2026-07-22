#!/usr/bin/env bash
set -euo pipefail
ENDPOINT="${MINIO_ENDPOINT:-http://127.0.0.1:9000}"
USER="${MINIO_ROOT_USER:-minio}"
PASS="${MINIO_ROOT_PASSWORD:-minio_dev_change_me}"
mc alias set local "$ENDPOINT" "$USER" "$PASS" >/dev/null
echo "=== raw/tlc ==="
mc ls --recursive "local/raw/tlc/" || true
echo "=== raw/weather ==="
mc ls --recursive "local/raw/weather/" || true
