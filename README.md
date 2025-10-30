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

AWS / EKS provisioning (what I added)
- `infra/terraform/` — Terraform skeleton that provisions a minimal EKS cluster using the `terraform-aws-modules/eks/aws` module. It's configured for a single small node (default `t3.small`, `node_count=1`) to keep AWS costs low. You must supply AWS credentials and region as GitHub secrets to run the automation.
- `.github/workflows/terraform-apply.yml` — GitHub Actions workflow that runs the Terraform apply and then bootstraps `cert-manager` and `ArgoCD` into the new cluster via Helm. The workflow is triggered manually (workflow_dispatch).
- `infra/argocd/argocd-application.yaml` — an ArgoCD Application manifest that points ArgoCD at `infra/k8s` in this repository so your infra manifests are managed by ArgoCD.

Required GitHub secrets for automation (add these to the repository Settings → Secrets):
- `AWS_ACCESS_KEY_ID` (IAM credentials with permissions to create EKS, VPC, EC2)
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (e.g., `us-east-1`)

Optional (for Cert-manager DNS01 with Route53):
- `ROUTE53_ZONE_ID` (if you want to enable DNS-01 challenges automatically — not wired into the workflow by default)

How to provision (safe flow):
1. Add the required GitHub secrets above.
2. From the Actions tab, run the `Infra — Terraform apply & bootstrap` workflow (manual dispatch). It will:
  - Terraform apply the minimal EKS cluster
  - Install `cert-manager` and `ArgoCD` into the cluster (Helm)
  - Apply an ArgoCD Application manifest which will cause ArgoCD to sync k8s manifests from `infra/k8s`

Important notes about costs and access:
- EKS control plane is a managed AWS service and has its own cost. The Terraform config provisions a single small worker node to keep the hourly cost minimal. Review AWS pricing before applying.
- The workflow will need AWS credentials with sufficient IAM permissions. If you prefer to run Terraform locally, you can run the Terraform in `infra/terraform` yourself and then run the Helm install steps locally.

OIDC (recommended) — automatic, no static keys
---------------------------------------------
To avoid storing static AWS keys in repo secrets, configure GitHub OIDC and an IAM role in your AWS account that trusts GitHub Actions. Then add the role ARN to the repository secret `AWS_ROLE_ARN`.

When `AWS_ROLE_ARN` is present the Actions workflow will attempt to assume that role via OIDC and proceed with Terraform/Helm without any `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` in the repo. If the secret is not present, the workflow falls back to using static keys.

If you'd like help creating the IAM role trust policy or a minimal policy document for the role, tell me which AWS account/organisational constraints you have and I can generate the policy text for you.

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
