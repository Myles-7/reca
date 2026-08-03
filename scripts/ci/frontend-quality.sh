#!/usr/bin/env bash
set -euo pipefail

cd frontend
bun install --frozen-lockfile
bun run format:check
bun run lint
bun run generate-client
bun run check-generated-client
bun run check:ui-boundaries
bun run build
git diff --exit-code -- src/api/generated
