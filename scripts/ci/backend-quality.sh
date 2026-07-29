#!/usr/bin/env bash
set -euo pipefail

uv sync --frozen --all-groups
uv run ruff format --check backend
uv run ruff check backend
uv run mypy backend/app
uv run pytest backend/tests -m no_database
