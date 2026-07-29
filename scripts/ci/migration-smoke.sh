#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must point to an isolated PostgreSQL service}"
export PROJECT_NAME=RECA ENVIRONMENT=test DEMO_MODE=false LOG_LEVEL=WARNING
export SECRET_KEY="${SECRET_KEY:-ci-only-secret-key-not-for-production-0123456789}"
export FIRST_SUPERUSER=m0-migration@example.com FIRST_SUPERUSER_PASSWORD="${FIRST_SUPERUSER_PASSWORD:-ci-only-password-not-for-production}"
export POSTGRES_SERVER=localhost POSTGRES_PORT="${POSTGRES_PORT:-5432}" POSTGRES_DB="${POSTGRES_DB:-reca_ci}" POSTGRES_USER="${POSTGRES_USER:-reca}" POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-reca_ci_password}"
export VALKEY_URL=valkey://localhost:6379/0 MINIO_ENDPOINT=http://localhost:9000 MINIO_ROOT_USER=ci-minio-user MINIO_ROOT_PASSWORD=ci-minio-password GROBID_URL=http://localhost:8070

cd backend
uv run alembic upgrade head
uv run alembic upgrade head
uv run python -c "from app.core.db import engine; from sqlalchemy import text; assert engine.connect().execute(text(\"SELECT extname FROM pg_extension WHERE extname = 'vector'\")).scalar_one() == 'vector'"
