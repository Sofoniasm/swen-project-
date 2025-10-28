#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
. .venv/Scripts/activate
python -m ai_engine.simulator --mode http --interval 5 --backend http://127.0.0.1:8000
