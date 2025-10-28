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
