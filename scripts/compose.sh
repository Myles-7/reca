#!/usr/bin/env sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
env_file="$root/.env"
if [ ! -f "$env_file" ]; then
  env_file="$root/.env.example"
fi

action=${1:?usage: scripts/compose.sh {config|build|up|ps|logs|restart|down}}
case "$action" in
  config) command='config' ;;
  build) command='build --pull' ;;
  up) command='up -d --build' ;;
  ps) command='ps' ;;
  logs) command='logs --no-color --tail 100' ;;
  restart) command='restart' ;;
  down) command='down' ;;
  *) echo "unknown action: $action" >&2; exit 2 ;;
esac

cd "$root"
# shellcheck disable=SC2086
exec docker compose --env-file "$env_file" $command
