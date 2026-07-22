# RainLift — local orchestration shortcuts
#
# make down — Stops containers and removes networks created by this Compose project.
#             Named volumes are left on disk so MinIO/Mongo data persists across runs.
#             To remove those volumes as well (destructive): docker compose down -v

PYTHONPATH := src
export PYTHONPATH

.PHONY: up down ingest curate quality mart test

up:
	docker compose up -d

down:
	docker compose down
	@echo "Volumes: named volumes were kept. Use 'docker compose down -v' to remove them."

ingest:
	python -m rainlift.ingest

curate:
	python -m rainlift.curate

quality:
	python -m rainlift.quality.run_ge

mart:
	python -m rainlift.marts

test:
	pytest
	docker compose config
