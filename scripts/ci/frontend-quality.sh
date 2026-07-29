#!/usr/bin/env bash
set -euo pipefail

cd frontend
bun install --frozen-lockfile
bun run format:check
bun run lint
bun run build
bun run generate-client
sed -i 's/[[:blank:]]*$//' src/client/*.gen.ts
git diff --exit-code -- src/client
