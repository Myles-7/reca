#!/usr/bin/env bash
set -euo pipefail

export COMPOSE_PROJECT_NAME="reca-ci-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-0}"
export SECRET_KEY="${SECRET_KEY:-ci-only-secret-key-not-for-production-0123456789}"
export FIRST_SUPERUSER=ci@example.invalid FIRST_SUPERUSER_PASSWORD="${FIRST_SUPERUSER_PASSWORD:-ci-only-password-not-for-production}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-reca_ci_password}" MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-ci-minio-password}"
export MODEL_API_KEY= OPENALEX_API_KEY=

cleanup() { docker compose down -v --remove-orphans; }
trap cleanup EXIT

docker compose config -q
docker compose build api worker frontend
docker compose up -d postgres valkey minio grobid api worker frontend
docker compose ps
for endpoint in live ready dependencies; do curl --fail --silent --show-error "http://127.0.0.1:8000/api/v1/health/${endpoint}" >/dev/null; done
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -c "from sqlalchemy import text; from app.core.db import engine; assert engine.connect().execute(text(\"SELECT 1 FROM pg_extension WHERE extname = 'vector'\")).scalar_one() == 1"
docker compose exec -T worker celery -A app.core.celery:celery_app inspect ping
