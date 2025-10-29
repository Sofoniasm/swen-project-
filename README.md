# AIOPS — Local dev & deploy notes

This repo contains a simple FastAPI backend, a static frontend, and a small `ai_engine` simulator that emits telemetry and decisions.

Quick local run (no docker-compose required):

1. Build and start the backend and frontend (uses Docker):

```bash
cd <repo-root>
./scripts/start_local.sh
```

2. Start the simulator (option A: run in a disposable container):

```bash
docker run -d --name aiops-simulator -v "$(pwd)":/app -e PYTHONPATH=/app python:3.11-slim \
  sh -c "python -m pip install -r /app/api/requirements.txt -q || true; \
  python -m ai_engine.simulator --mode http --interval 2 --backend http://host.docker.internal:8001"
```

Option B: run the simulator locally (requires Python and dependencies):

```bash
python -m pip install -r api/requirements.txt
python -m ai_engine.simulator --mode http --interval 2 --backend http://127.0.0.1:8001
```

CI and Registry
---------------

A GitHub Actions workflow (`.github/workflows/ci-build-push.yml`) is included and configured to push images to GitHub Container Registry (GHCR). To push images from the workflow, ensure the repository has `GITHUB_TOKEN` (default) or set up a personal access token with `packages: write` if needed.

Kubernetes & GitOps
-------------------

There are K8s manifests under `infra/k8s/` (backend/frontend deployment, services, ingress). They include placeholders for image names and hostnames. Add your domain to the Ingress host and configure cert-manager with a ClusterIssuer for Let's Encrypt.

Next steps I can do for you:
- Finalize CI to push to another registry (ECR/Docker Hub) if you prefer.
- Prepare Terraform modules to provision EKS + ArgoCD + cert-manager (requires AWS credentials and domain access).
- Automatically update k8s image tags from CI and create an ArgoCD Application manifest.
# SWEN GitOps + AIOps Prototype

This repository contains a simulation-first GitOps + AIOps prototype for SWEN.

Quick start (bootstrap everything locally):

Git Bash / Linux

```bash
./scripts/bootstrap.sh
```

PowerShell (Windows)

```powershell
.\scripts\bootstrap.ps1
```

After bootstrap:
- Backend: http://localhost:8000
- Frontend: http://localhost:8080

Run the simulator locally (without Docker):

```bash
./.venv/Scripts/python.exe -m ai_engine.simulator --mode http --interval 5
```

Run the AI->Git operator in dry-run:

```bash
./.venv/Scripts/python.exe scripts/ai_git_operator.py --once
```

CI: a GH Actions workflow at `.github/workflows/terraform_plan.yml` will run `terraform plan` for changes in `infra/`.

Terraform in this repo is simulation-first by default (variable `simulate = true` in `infra/main.tf`).
