#!/usr/bin/env bash
set -euo pipefail

git diff --check
test -f THIRD_PARTY_NOTICES.md
test -f vendor/licenses/full-stack-fastapi-template-LICENSE.txt
tracked_env_files=$(git ls-files -- .env '.env.*' | grep -Ev '^\.env\.example$' || true)
if [ -n "$tracked_env_files" ]; then echo "tracked .env file detected" >&2; exit 1; fi
if git ls-files '*.pem' '*.key' | grep -q .; then echo "tracked private-key-like file detected" >&2; exit 1; fi
if rg -n --glob 'Dockerfile*' --glob 'docker-compose*.yml' '(FROM|image:) .*:latest\b' .; then echo "floating latest image tag detected" >&2; exit 1; fi
if rg -n --glob '!docs/source-research/**' --glob '!**/.git/**' 'D:\\桌面\\Recas\\upstream-lab|\.\./upstream-lab' .; then echo "upstream-lab runtime path detected" >&2; exit 1; fi
if rg -n --glob '!uv.lock' --glob '!bun.lock' --glob '!docs/**' --glob '!**/.git/**' 'AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----' .; then echo "potential credential detected" >&2; exit 1; fi
PYTHONUTF8=1 uv run pip-audit
audit_log=$(mktemp)
trap 'rm -f "$audit_log"' EXIT
if (cd frontend && bun audit) >"$audit_log" 2>&1; then
  cat "$audit_log"
else
  cat "$audit_log"
  if grep -Eq '[0-9]+ vulnerabilities \([0-9]+ low\)' "$audit_log" && ! grep -Eqi '\b(critical|high|moderate)\b' "$audit_log"; then
    echo "PASS_WITH_LOW_ADVISORY: retained Babel 7 LOW advisory is recorded in M0-ISSUE-0006." >&2
  else
    exit 1
  fi
fi
uv run zizmor .
