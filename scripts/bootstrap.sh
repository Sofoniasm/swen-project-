#!/usr/bin/env bash
set -euo pipefail

# Bootstrap development environment (Git Bash / Linux)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# 1) Python venv
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
. .venv/Scripts/activate
python -m pip install --upgrade pip
if [ -f api/requirements.txt ]; then
  pip install -r api/requirements.txt
fi

# 2) Node frontend build
if [ -d frontend ]; then
  if [ -f frontend/package.json ]; then
    (cd frontend && npm ci)
    (cd frontend && npm run build)
  fi
fi

# 3) Docker compose build & up
docker-compose build --pull
# start services in background
docker-compose up -d

echo "Bootstrap complete. Backend: http://localhost:8000 healthz, Frontend: http://localhost:8080"
