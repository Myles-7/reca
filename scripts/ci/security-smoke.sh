#!/usr/bin/env bash
set -euo pipefail

git diff --check
test -f THIRD_PARTY_NOTICES.md
test -f vendor/licenses/full-stack-fastapi-template-LICENSE.txt
if git ls-files --error-unmatch .env >/dev/null 2>&1 || git ls-files '*.env' '.env.*' | grep -q .; then echo "tracked .env file detected" >&2; exit 1; fi
if git ls-files '*.pem' '*.key' | grep -q .; then echo "tracked private-key-like file detected" >&2; exit 1; fi
if rg -n --glob 'Dockerfile*' --glob 'docker-compose*.yml' '(FROM|image:) .*:latest\b' .; then echo "floating latest image tag detected" >&2; exit 1; fi
if rg -n --glob '!docs/source-research/**' --glob '!**/.git/**' 'D:\\桌面\\Recas\\upstream-lab|\.\./upstream-lab' .; then echo "upstream-lab runtime path detected" >&2; exit 1; fi
if rg -n --glob '!uv.lock' --glob '!bun.lock' --glob '!docs/**' --glob '!**/.git/**' 'AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----' .; then echo "potential credential detected" >&2; exit 1; fi
PYTHONUTF8=1 uv run pip-audit
(cd frontend && bun audit)
uv run zizmor .
