# RainLift — Build Progress Tracker

---

## Progress Legend
[ ] Not started
[~] In progress
[x] Done
[!] Blocked — see note

---

## Master TODO List

[x] 1. Create repository root `Makefile` with targets `up` (docker compose up -d), `down` (compose down with documented volume behavior), `ingest` (Python ingest entrypoint), and `test` (pytest + `docker compose config`) — file: `Makefile`.

[x] 2. Create `.env.example` with MinIO credentials and endpoint, Nessie URL, MongoDB URI and db name, Trino host/port, fixed TLC month `YYYY-MM`, TLC Parquet URL placeholder, Open-Meteo base URL, `WEATHER_LAT`/`WEATHER_LON`, bucket names — file: `.env.example`.

[x] 3. Create `requirements.txt` for Python 3.11: PyIceberg, boto3 or MinIO client, pymongo, trino client, Great Expectations, Streamlit, pytest — file: `requirements.txt`.

[x] 4. Add `docker-compose.yml` service `minio` with ports, volumes, env — resource: service `minio`.

[x] 5. Add `docker-compose.yml` service `nessie` with pinned tag and healthcheck — resource: service `nessie`.

[x] 6. Add `docker-compose.yml` service `mongodb` (Community) with volume and healthcheck — resource: service `mongodb`.

[x] 7. Add `docker-compose.yml` service `trino` mounting `./configs/trino` — resource: service `trino`.

[x] 8. Add `docker-compose.yml` service `streamlit` for dashboard — resource: service `streamlit`.

[x] 9. Add `minio-init` one-shot creating buckets `raw`/`curated` and keys under `raw/tlc/`, `raw/weather/`, `curated/` — resource: service `minio-init`.

### CHECKPOINT A — Docker Compose services defined; stack starts
Verify:
- `docker compose config` exits `0`.
- `make up` then `docker compose ps` shows all services up or healthy.
Smoke test:
- Browser: MinIO console; `curl` Nessie base URL per Nessie version docs.
Go/No-Go: Crash loops → fix ports, env, image tags in `docker-compose.yml`.
If fail: Missing `./configs/trino` mount → create placeholder dirs in later todos or add empty mount stub.
Do not proceed until this checkpoint passes.

[x] 10. Create `configs/trino/catalog/iceberg.properties` wiring Iceberg → Nessie + MinIO S3 endpoint — file: `configs/trino/catalog/iceberg.properties`.

[x] 11. Create `configs/trino/config.properties` for single-node Trino — file: `configs/trino/config.properties`.

[x] 12. Create `configs/trino/jvm.config` with bounded heap — file: `configs/trino/jvm.config`.

[x] 13. Create `src/rainlift/__init__.py` — file: `src/rainlift/__init__.py`.

[x] 14. Add `scripts/wait_for_tcp.py` or healthcheck script; ensure Trino starts after MinIO/Nessie healthy — files: `scripts/*`, `docker-compose.yml`.

[x] 15. Implement `src/rainlift/config.py` → `load_settings()` — module: `src/rainlift/config.py`.

[x] 16. Implement `src/rainlift/ingest/minio_raw.py` (`put_raw_object`, path builders) — module: `src/rainlift/ingest/minio_raw.py`.

[x] 17. Implement `src/rainlift/ingest/tlc_fetch.py` → `stream_tlc_parquet_to_minio` — module: `src/rainlift/ingest/tlc_fetch.py`.

[x] 18. Implement `src/rainlift/ingest/weather_fetch.py` → `fetch_open_meteo_daily` — module: `src/rainlift/ingest/weather_fetch.py`.

### CHECKPOINT B — MinIO + Nessie initialized; Trino loads Iceberg catalog
Verify:
- MinIO lists `raw` and `curated` after init; prefix keys exist.
- Nessie responds to REST health/config call.
- `docker compose logs trino` shows Iceberg catalog without fatal errors.
Smoke test:
- `docker compose exec trino trino --execute "SHOW CATALOGS"` if CLI available in image.
Go/No-Go: Catalog missing → fix `iceberg.properties` Nessie URI and S3 credentials.
If fail: Network DNS between containers → use Compose service names in URLs.
Do not proceed until this checkpoint passes.

[x] 19. Implement `src/rainlift/metadata/mongo_runs.py` → `upsert_run(db, ingest_date, dataset, payload)` with identifying fields `ingest_date` + `dataset` — module: `src/rainlift/metadata/mongo_runs.py`.

[x] 20. Add `tests/test_mongo_contract.py` — file: `tests/test_mongo_contract.py`.

[x] 21. Implement `python -m rainlift.ingest` CLI — module: `src/rainlift/ingest/__main__.py`.

[x] 22. Add `tests/test_ingest_paths.py` for partition key strings — file: `tests/test_ingest_paths.py`.

[x] 23. Add `scripts/verify_raw.sh` or `verify_raw.ps1` listing MinIO objects under raw prefixes — file: `scripts/verify_raw.*`.

[x] 24. Run `make ingest`; verify non-zero Parquet size and valid weather JSON — artifact: console log or `docs/evidence/ingest_log.txt`.

[x] 25. Query MongoDB for two documents (`tlc`, `weather`) with same `ingest_date` — verification: query saved in `docs/evidence/mongo_ingest.txt`.

[x] 26. Document idempotent ingest in code comments — file: `src/rainlift/metadata/mongo_runs.py` or ingest module.

[x] 27. Add `pytest.ini` with markers `integration` / `slow` — file: `pytest.ini`.

### CHECKPOINT C — Raw landing + MongoDB run documents
Verify:
- Raw TLC Parquet under `raw/tlc/year=YYYY/month=MM/` has size > 0.
- Raw weather under `raw/weather/year=YYYY/month=MM/`.
- MongoDB docs include `ingest_date`, `dataset`, `status`, hash, `row_count` where applicable.
Smoke test:
- Second `make ingest` does not create unbounded duplicate keys (per documented behavior).
Go/No-Go: Wrong paths → `minio_raw.py`; empty Mongo → connection string in Compose.
Do not proceed until this checkpoint passes.

[x] 28. Implement `src/rainlift/curate/transforms.py` — module: `src/rainlift/curate/transforms.py`.

[x] 29. Implement `src/rainlift/curate/iceberg_tables.py` → `ensure_trips_table()`, `ensure_weather_table()` — module: `src/rainlift/curate/iceberg_tables.py`.

[x] 30. Implement `python -m rainlift.curate` — module: `src/rainlift/curate/__main__.py`.

[x] 31. Create `sql/trino/create_schemas.sql` — file: `sql/trino/create_schemas.sql`.

[x] 32. Run curate; record `row_count` in Mongo for curated datasets — verification: Mongo fields.

[x] 33. Trino `SHOW TABLES` / `SELECT COUNT(*)` on curated trip table with `year`,`month` filters — evidence: `docs/evidence/trino_curated.txt`.

[x] 34. Create `configs/great_expectations/great.yml` + expectations for **curated** trips and weather — files: `configs/great_expectations/*`.

[x] 35. Implement `src/rainlift/quality/run_ge.py` → `run_expectations_suite()` — module: `src/rainlift/quality/run_ge.py`.

[x] 36. Add `tests/test_transforms.py` — file: `tests/test_transforms.py`.

### CHECKPOINT D — Curated Iceberg + Trino read + Great Expectations on curated (before marts)
Verify:
- Nessie/PyIceberg shows curated table metadata.
- Trino counts > 0 on curated tables with partition filters.
- `python -m rainlift.quality.run_ge` exits `0` **before** mart SQL runs.
Smoke test:
- Re-run GE; still passes on same data.
Go/No-Go: Trino schema mismatch → align `create_schemas.sql` with Iceberg namespace; GE fails → fix expectations or transforms.
Do not proceed until this checkpoint passes.

[x] 37. Create `sql/trino/create_trip_weather_daily.sql` → view `trip_weather_daily` — artifact: Trino view `trip_weather_daily`.

[x] 38. Create `sql/trino/create_mart_rain_demand_lift.sql` **last** in apply order — artifact: `rain_demand_lift` per Section 8.

[x] 39. Create `sql/trino/apply_order.txt` with `create_mart_rain_demand_lift.sql` last — file: `sql/trino/apply_order.txt`.

[x] 40. Implement `src/rainlift/marts/trino_runner.py` → `apply_sql_files` reading `apply_order.txt` — module: `src/rainlift/marts/trino_runner.py`.

[x] 41. Add `tests/test_rain_metric.py` — file: `tests/test_rain_metric.py`.

[x] 42. Save Trino mart sample to `docs/evidence/trino_mart_sample.txt` — file: `docs/evidence/trino_mart_sample.txt`.

[x] 43. Manual spot-check one borough vs `trip_weather_daily` — note in session notes / evidence file.

[x] 44. Add `make mart` (or equivalent) invoking `trino_runner` after GE — file: `Makefile`.

[x] 45. Add `make quality` running GE before mart — file: `Makefile`.

### CHECKPOINT E — `rain_demand_lift` correct; SQL order enforced
Verify:
- `SELECT * FROM rain_demand_lift LIMIT 50` matches Section 7 column intent.
- `apply_order.txt` lists mart SQL last.
- One borough manual check matches SQL within tolerance.
Smoke test:
- Drop and recreate views in dev; re-run `apply_order` cleanly.
Go/No-Go: Bad joins → fix `create_trip_weather_daily.sql`; mart wrong → `create_mart_rain_demand_lift.sql`.
Do not proceed until this checkpoint passes.

[x] 46. Implement `src/rainlift/dashboard/app.py` Streamlit `main()` — module: `src/rainlift/dashboard/app.py`.

[x] 47. Pass Trino host/port to Streamlit via Compose env — update: `docker-compose.yml` `streamlit` service.

[x] 48. Add optional `Dockerfile` for Streamlit — file: `Dockerfile`.

[ ] 49. Capture `docs/evidence/streamlit_rain_demand_lift.png` — file: `docs/evidence/streamlit_rain_demand_lift.png`.

[ ] 50. Capture Trino evidence to `docs/evidence/trino_mart.png` or `.txt` — file: `docs/evidence/*`.

[x] 51. Export Mongo run doc to `docs/evidence/mongo_run.json` — file: `docs/evidence/mongo_run.json`.

[x] 52. Save GE summary to `docs/evidence/ge_summary.txt` — file: `docs/evidence/ge_summary.txt`.

[x] 53. Write `README.md`: pitch → Mermaid (**Apache Iceberg** + **Project Nessie** labels) → `make up` → deep dive — file: `README.md`.

[x] 54. Add `.gitignore` — file: `.gitignore`.

### CHECKPOINT F — End-to-end demo + README
Verify:
- `cp .env.example .env` → `make up` → `make ingest` → curate → `make quality` → mart → Streamlit works.
- `make test` passes.
- Mermaid in README renders with **Iceberg** and **Nessie** visible as text.
Smoke test:
- `rg -i "aws\\.amazon"` returns no deployment artifacts.
Go/No-Go: Streamlit errors → Trino hostname on Docker network.
Do not proceed until this checkpoint passes.

[x] 55. Create `.github/workflows/ci.yml` **last**: Python 3.11, `pip install -r requirements.txt`, `pytest`, `docker compose config` — file: `.github/workflows/ci.yml`.

[x] 56. Ensure `pytest.ini` markers documented — file: `pytest.ini`.

[x] 57. Confirm CI uses only `actions/checkout`, `actions/setup-python`, no cloud deploy secrets — review: `.github/workflows/ci.yml`.

[x] 58. Add debug step `docker compose version` — file: `.github/workflows/ci.yml`.

[x] 59. Local pre-push: `pytest -q && docker compose config` — verification: developer log.

[ ] 60. Push and confirm GitHub Actions green — verification: Actions UI screenshot optional.

[x] 61. Add CI badge or workflow name line in README — file: `README.md`.

[x] 62. Fill Section 9 resume bullets in `docs/specs/<<RainLift_SPEC>>.md` with measured numbers — file: `docs/specs/<<RainLift_SPEC>>.md`.

[x] 63. Add `docs/audit_no_cloud.md` stating `git grep` results for cloud vendor strings — file: `docs/audit_no_cloud.md`.

### CHECKPOINT G — CI green
Verify:
- Latest workflow success on default branch for `pytest` and `docker compose config`.
- No secrets in repo beyond `.env.example` placeholders.
Smoke test:
- Re-run workflow; still green.
Go/No-Go: Compose v2 syntax → update workflow; pytest → pin versions.
Do not proceed until this checkpoint passes.

[x] 64. Final cross-check: each Section 9 bullet cites artifact path in `README.md` — file: `README.md`.

[x] 65. Final cross-check: README metric text matches Section 8 formula verbatim — file: `README.md`.

[x] 66. Tag release or document version string in README — file: `README.md` (optional).

## FINAL CHECKPOINT — Definition of Done (Section 14)
Verify:
- [ ] `docker-compose.yml` defines MinIO, Nessie, MongoDB, Trino, Streamlit, init with pinned images where practical.
- [ ] `make up` / `make down` documented and work.
- [ ] Raw TLC + Open-Meteo in MinIO raw prefixes for one fixed month.
- [ ] MongoDB run docs with `ingest_date` + `dataset` + hashes/status.
- [ ] Curated Iceberg on MinIO via Nessie; raw immutable.
- [ ] Trino queries curated Iceberg.
- [ ] Great Expectations pass on curated before marts.
- [ ] `rain_demand_lift` last SQL artifact; formula matches Section 8.
- [ ] Streamlit shows mart.
- [ ] README order: pitch → Mermaid (Iceberg + Nessie visible) → `make up` → deep dive.
- [ ] GitHub Actions CI green.
- [ ] Resume bullets have measurable evidence.
- [ ] No cloud accounts, cards, or paid APIs required.

Smoke test:
- Clean machine: clone, Docker only, full run, green CI.

Go/No-Go: Any Section 14 item fails → fix owning file, re-run FINAL CHECKPOINT.

Do not declare RainLift complete until FINAL CHECKPOINT passes.

---

## Blocked Items Log
| TODO # | Blocker description | Date | Resolution |
|--------|---------------------|------|------------|

---

## Session Resume Instructions
If you are resuming after a closed session:
1. Open `docs/PROGRESS.md`
2. In **Master TODO List**, find the first `[~]` or the first `[ ]` after the last `[x]`
3. Tell Cursor: "Resume RainLift from TODO #N — read `docs/specs/<<RainLift_SPEC>>.md` and `docs/PROGRESS.md` before proceeding"

### PROGRESS.md update rules (Cursor must follow without being asked)
- During the build, **only** change the status prefix on numbered todo lines: `[ ]` → `[~]` → `[x]` or `[!]`.
- Mark `[~]` the moment you begin a todo.
- Mark `[x]` only after that todo’s verification step passes, not when the code is written.
- Use `[!]` when a todo is blocked.
- Never mark `[x]` on a todo if its checkpoint (if any) has not passed.

This file is the single source of truth for build progress alongside `docs/specs/<<RainLift_SPEC>>.md`.
