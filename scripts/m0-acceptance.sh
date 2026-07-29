#!/usr/bin/env bash
set -uo pipefail

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONUTF8=1
project="reca_m0_acceptance"
evidence_root="${TMPDIR:-/tmp}/reca-m0-acceptance-$(date +%Y%m%d-%H%M%S)"
env_file="$evidence_root/acceptance.env"
mkdir -p "$evidence_root"
trap 'docker compose --project-name "$project" --env-file "$env_file" down -v --remove-orphans >/dev/null 2>&1 || true; rm -f "$env_file"' EXIT

step() { local name=$1; shift; if "$@" >"$evidence_root/$name.log" 2>&1; then printf 'PASS %s\n' "$name"; else printf 'FAIL %s (see %s/%s.log)\n' "$name" "$evidence_root" "$name"; failures=1; fi; }
not_run() { printf 'NOT_RUN %s\n' "$1"; printf '%s\n' "$2" >"$evidence_root/$1.log"; }
failures=0
secret=$(openssl rand -base64 48 | tr -d '\n')
cat >"$env_file" <<EOF
PROJECT_NAME=RECA
ENVIRONMENT=test
DEMO_MODE=false
SECRET_KEY=$secret
FIRST_SUPERUSER=acceptance@example.com
FIRST_SUPERUSER_PASSWORD=acceptance-admin-$(openssl rand -hex 16)
POSTGRES_DB=reca_acceptance
POSTGRES_USER=reca_acceptance
POSTGRES_PASSWORD=acceptance-pg-$(openssl rand -hex 16)
MINIO_ROOT_USER=reca-acceptance
MINIO_ROOT_PASSWORD=acceptance-minio-$(openssl rand -hex 16)
MINIO_BUCKET=reca-acceptance
MODEL_API_KEY=
OPENALEX_API_KEY=
API_PORT=18000
FRONTEND_PORT=15173
VITE_API_URL=http://127.0.0.1:18000
VITE_APP_ENV=test
VITE_DEMO_MODE=false
FRONTEND_HOST=http://127.0.0.1:15173
BACKEND_CORS_ORIGINS=["http://127.0.0.1:15173"]
EOF
cd "$root"
docker compose --project-name "$project" --env-file "$env_file" down -v --remove-orphans >/dev/null 2>&1 || true
step git-status git status --short
step tool-versions bash -c 'docker --version; docker compose version; python --version; bun --version; python -m uv --version'
step locked-inputs sha256sum pyproject.toml uv.lock package.json bun.lock
step compose-config docker compose --project-name "$project" --env-file "$env_file" config -q
step build-images docker compose --project-name "$project" --env-file "$env_file" build api worker frontend
if [ "$failures" -eq 0 ]; then
  step start-services docker compose --project-name "$project" --env-file "$env_file" up -d postgres valkey minio grobid api worker frontend
  step migrations docker compose --project-name "$project" --env-file "$env_file" exec -T api alembic upgrade head
  step migrations-repeat docker compose --project-name "$project" --env-file "$env_file" exec -T api alembic upgrade head
  step health-live curl --fail --silent --show-error http://127.0.0.1:18000/api/v1/health/live
  step health-ready curl --fail --silent --show-error http://127.0.0.1:18000/api/v1/health/ready
  step health-dependencies curl --fail --silent --show-error http://127.0.0.1:18000/api/v1/health/dependencies
  step worker-ping docker compose --project-name "$project" --env-file "$env_file" exec -T worker celery -A app.core.celery:celery_app inspect ping
else
  not_run start-services "Blocked by isolated build failure."
  not_run runtime-acceptance "Blocked by isolated build failure."
fi
step backend-tests python -m uv run pytest backend/tests -m no_database
step frontend-quality bun run --cwd frontend build
step playwright-shell bash -c 'cd frontend && bunx playwright test -c playwright.shell.config.ts --reporter=list'
step python-security-audit python -m uv run pip-audit
step node-security-audit bun audit
exit "$failures"
