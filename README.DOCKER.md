# Docker & CI Quickstart

This file documents the quick steps to build and run the project using Docker and how to push to GitHub to trigger CI.

Run locally with docker-compose

1. Build and start services (frontend served at http://localhost:8000, backend at http://localhost:8001):

```bash
docker-compose up --build -d
```

2. Tail logs:

```bash
docker-compose logs -f frontend
docker-compose logs -f backend
```

3. Stop services:

```bash
docker-compose down
```

Commit & push to GitHub

1. Add files and commit locally:

```bash
git add Dockerfile.frontend docker-compose.yml .github/workflows/ci.yml README.DOCKER.md
git commit -m "chore: add docker-compose, frontend Dockerfile and CI workflow"
```

2. Push to your repository (example remote):

```bash
git remote add origin https://github.com/Sofoniasm/swen-project-.git
git branch -M main
git push -u origin main
```

Repository secrets for image publishing (optional)

- To publish images to GitHub Container Registry, add `GHCR_TOKEN` in your repo Settings → Secrets → Actions (a personal access token with write:packages and read:packages).
- Alternatively, add Docker Hub credentials `DOCKER_USERNAME` and `DOCKER_PASSWORD` and modify the workflow accordingly.

Notes

- docker-compose maps host port 8000 → frontend, and 8001 → backend to avoid conflicts with local development servers. Adjust `docker-compose.yml` if you need different ports.
