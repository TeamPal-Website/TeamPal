#!/usr/bin/env bash
set -euo pipefail
exec docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build "$@"
