# Failure notes — bugs that actually happened

Short post-mortems from proving RainLift E2E on Windows + Docker Desktop (2026-07-24). Useful when someone asks “what broke?”

## 1. Host `.env` poisoned Streamlit Trino DNS

**Symptom:** Streamlit could not reach Trino / empty dashboard while `docker compose exec trino …` worked.

**Cause:** Compose interpolated `TRINO_HOST=localhost` from host `.env` into the Streamlit container. Inside the network, Trino is service name `trino`, not localhost.

**Fix:** Keep host `.env.example` on `localhost` for optional host Python. Hardcode Streamlit / pipeline service env to `TRINO_HOST=trino`, `TRINO_PORT=8080` in `docker-compose.yml`.

## 2. Port 8080 already taken (Airflow)

**Symptom:** Trino publish failed or collided with another stack.

**Cause:** Local Airflow (SkyOps / others) already bound host `8080`.

**Fix:** Map Trino to host **8088** (`8088:8080`). Containers still use `trino:8080`.

## 3. Windows CRLF broke shell scripts and Trino props

**Symptom:** `minio-init.sh` failed on `set -eu`; Trino ignored or mis-parsed `node.data-dir`.

**Cause:** CRLF line endings (`\r`) on scripts and `configs/trino/*.properties`.

**Fix:** Normalize to LF (`scripts/fix_lf.py` / editor). Prefer `.gitattributes` `*.sh text eol=lf` and `*.properties text eol=lf` going forward.

## 4. Trino `node.data-dir` not writable

**Symptom:** Trino unhealthy / cannot create data directory.

**Cause:** Config pointed at root-owned `/data` in the image.

**Fix:** Use `/data/trino` (writable in `trinodb/trino:453`).

## 5. Trino OOM / memory config

**Symptom:** Queries aborted or coordinator unstable under Iceberg scans.

**Cause:** `query.max-memory-per-node` set above usable heap after JVM headroom.

**Fix:** Keep per-node query memory ≤ heap − headroom in `configs/trino/config.properties` / `jvm.config`.

## 6. Iceberg + Nessie catalog wiring

**Symptom:** PyIceberg / Trino could not resolve warehouse or catalog.

**Cause:** Wrong property names (`warehouse` vs `default-warehouse-dir`); PyIceberg 0.7 has no `type=nessie` — use Iceberg REST against Nessie with MinIO warehouse props.

**Fix:** Nessie `application.properties` warehouse → `s3://curated/wh/`; Trino `iceberg.properties` aligned; PyIceberg REST catalog.

## 7. Nanosecond timestamps rejected on Iceberg write

**Symptom:** Curate failed writing TLC pickup/dropoff timestamps.

**Cause:** Pandas/Parquet ns precision; Iceberg path expected µs.

**Fix:** Downcast timestamps to microseconds before write (`curate/transforms.py`).

## 8. Nessie does not support `CREATE VIEW`

**Symptom:** Mart SQL using views failed.

**Cause:** Nessie Iceberg REST catalog rejects views.

**Fix:** Materialize marts as Iceberg tables (`trip_weather_daily`, `rain_demand_lift`).

## 9. Pipeline container could not resolve TLC / Open-Meteo

**Symptom:** Ingest DNS failures for CloudFront / Open-Meteo from Compose network.

**Cause:** Docker Desktop DNS quirks on this host.

**Fix:** Set public DNS (`8.8.8.8`, `1.1.1.1`) on the `pipeline` service.

## 10. Great Expectations OOM on full TLC table

**Symptom:** GE hung / blew memory loading ~3M rows into pandas.

**Cause:** Full-table PandasDataset materialization.

**Fix:** Aggregate null audit in SQL + ~1% sample for row-level checks (`quality/run_ge.py`).

## 11. No host Python 3.11

**Symptom:** `make ingest` on host failed (system Python 3.14 / missing deps).

**Fix:** Default Makefile targets through Compose `pipeline` service (`HOST_PIPELINE=1` for local 3.11).

## 12. Stale `minio/mc` image tag

**Symptom:** `minio-init` image pull 404.

**Fix:** Pin `minio/mc:RELEASE.2024-10-08T09-37-26Z`.

## Related

- Recorded green run: [validation-log.md](validation-log.md)
- Spec: [specs/RAINLIFT_SPEC.md](specs/RAINLIFT_SPEC.md)
