#!/usr/bin/env bash
set -euo pipefail

# Build and run the backend and frontend locally using docker.
# This script is intended for development/demo purposes.

ROOT_DIR="$(pwd)"

echo "Building backend image..."
docker build -f Dockerfile.backend -t aiops-backend:local .

echo "Starting backend container on host port 8001..."
docker rm -f aiops-backend 2>/dev/null || true
docker run -d --name aiops-backend -p 8001:8000 -v "${ROOT_DIR}/api":/app/api:ro -e PYTHONUNBUFFERED=1 aiops-backend:local

if [ -d "${ROOT_DIR}/frontend/dist" ]; then
	echo "Building frontend image..."
	docker build -f Dockerfile.frontend -t aiops-frontend:local ./frontend

	echo "Starting frontend container on host port 8000..."
	docker rm -f aiops-frontend 2>/dev/null || true
	docker run -d --name aiops-frontend -p 8000:80 --link aiops-backend:backend aiops-frontend:local
	echo "Local stack started. Backend: http://127.0.0.1:8001  Frontend: http://127.0.0.1:8000"
else
	echo "No frontend build found at frontend/dist — skipping frontend container."
	echo "Backend started at http://127.0.0.1:8001"
fi
