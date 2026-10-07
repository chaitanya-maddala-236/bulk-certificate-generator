.PHONY: install run worker test lint format migrate docker-up docker-down

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.workers.celery_app.celery_app worker --loglevel=info

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down
