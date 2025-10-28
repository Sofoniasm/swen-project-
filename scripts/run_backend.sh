#!/usr/bin/env bash
# Run backend using venv python (Git Bash)
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "Creating venv"
  python -m venv .venv
fi
. .venv/Scripts/activate
python -m pip install --upgrade pip
if [ -f api/requirements.txt ]; then
  pip install -r api/requirements.txt
fi
# Run uvicorn
echo "Starting backend on http://127.0.0.1:8000"
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
