# RainLift — local orchestration shortcuts
#
# make down — Stops containers and removes networks created by this Compose project.
#             Named volumes are left on disk so MinIO/Mongo data persists across runs.
#             To remove those volumes as well (destructive): docker compose down -v
#
# Pipeline steps run inside Compose service `pipeline` (Python 3.11 image) so Windows
# hosts without a matching local interpreter still get a working demo path.
# Override with HOST_PIPELINE=1 to use local `python -m ...` instead (needs PYTHONPATH=src).

PYTHONPATH := src
export PYTHONPATH

HOST_PIPELINE ?= 0

ifeq ($(HOST_PIPELINE),1)
RUN_PY = python
else
RUN_PY = docker compose run --rm pipeline
endif

.PHONY: up down ingest curate quality mart lint test help

help:
	@echo "Targets: up down ingest curate quality mart lint test help"
	@echo "Pipeline defaults to docker compose run (set HOST_PIPELINE=1 for local python)."
	@echo "Faster re-demo: skip ingest/curate if MinIO volumes already hold Jan 2024 raw+curated;"
	@echo "  then only: make quality && make mart (or open Streamlit if mart exists)."

up:
	docker compose up -d --build

down:
	docker compose down
	@echo "Volumes: named volumes were kept. Use 'docker compose down -v' to remove them."

ingest:
	$(RUN_PY) -m rainlift.ingest

curate:
	$(RUN_PY) -m rainlift.curate

quality:
	$(RUN_PY) -m rainlift.quality.run_ge

mart:
	$(RUN_PY) -m rainlift.marts

lint:
	python -m ruff check .

test:
	pytest
	docker compose config
