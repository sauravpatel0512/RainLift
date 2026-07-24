# Validation log — local end-to-end run

Proof that MinIO → Iceberg (Nessie) → Trino → Great Expectations → mart → Streamlit works on a developer machine. Numbers from Trino / Mongo / MinIO on **2026-07-24** (artifacts under `docs/evidence/`).

## Run metadata

| Field | Value |
|-------|-------|
| Date | 2026-07-24 |
| Host | Windows 10 + Docker Desktop |
| Month | 2024-01 (pinned TLC yellow + Open-Meteo archive) |
| Stack | MinIO, Nessie 0.99, Trino 453, MongoDB 7, Streamlit, Compose `pipeline` |

## Demo path used

```text
docker compose up -d --build
docker compose run --rm pipeline -m rainlift.ingest
docker compose run --rm pipeline -m rainlift.curate
docker compose run --rm pipeline -m rainlift.quality.run_ge
docker compose run --rm pipeline -m rainlift.marts
# open http://localhost:8501
```

## Results

| Step | Result |
|------|--------|
| Ingest | `raw/tlc/.../yellow_tripdata_2024-01.parquet` (~50 MB); `raw/weather/.../open_meteo_daily.json` |
| Mongo | 4× `pipeline_runs` success (`tlc`, `weather`, `curated_tlc`, `curated_weather`) |
| Curate | `tlc_trips` **2,964,606** (Trino count); `weather_daily` **31** |
| Quality | GE OK — `tlc_trips n=2964624`, sample `29839`, weather `31` |
| Mart | `rain_demand_lift` — 8 borough/zone rows (Manhattan lift ≈ **0.984**) |
| UI | Streamlit `http://localhost:8501` HTTP 200 with mart table + bar chart |

## Evidence pointers

| Artifact | Path |
|----------|------|
| Trino curated counts | `docs/evidence/trino_curated.txt` |
| Mart sample + Manhattan daily spot-check | `docs/evidence/trino_mart_sample.txt` |
| Mongo runs | `docs/evidence/mongo_run.json` |
| GE summary | `docs/evidence/ge_summary.txt` |
| Streamlit screenshot | `docs/evidence/streamlit_rain_demand_lift.png` |
| Mart chart | `docs/evidence/rain_demand_lift_chart.png` |

## Notes

- Curated Mongo `row_count` for TLC (**2,964,624**) can differ slightly from Trino `count(*)` after filters/partition predicates — both are same order of magnitude for Jan 2024 yellow.
- Debugging write-up: [FAILURE_NOTES.md](FAILURE_NOTES.md).
