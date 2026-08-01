#!/usr/bin/env bash
set -euo pipefail

export COMPOSE_PROJECT_NAME="reca-ci-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-0}"
export SECRET_KEY="${SECRET_KEY:-ci-only-secret-key-not-for-production-0123456789}"
export FIRST_SUPERUSER=m0-compose@example.com FIRST_SUPERUSER_PASSWORD="${FIRST_SUPERUSER_PASSWORD:-ci-only-password-not-for-production}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-reca_ci_password}" MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-ci-minio-password}"
export MODEL_API_KEY= OPENALEX_API_KEY=

cleanup() {
  status=$?
  if (( status != 0 )); then
    docker compose ps -a || true
    docker compose logs --no-color api worker || true
  fi
  docker compose down -v --remove-orphans
  return "$status"
}
trap cleanup EXIT

docker compose config -q
docker compose build api worker frontend
docker compose up -d postgres valkey minio grobid api worker frontend
docker compose ps
python scripts/wait_for_http.py http://127.0.0.1:8000/api/v1/health/live --timeout 90
docker compose exec -T api alembic upgrade head
python scripts/wait_for_http.py http://127.0.0.1:8000/api/v1/health/ready --timeout 90
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/dependencies >/dev/null
docker compose exec -T api python -m app.cli.pgvector_smoke
docker compose exec -T worker celery -A app.core.celery:celery_app inspect ping
