RUNBOOK — Local dev & demo
=========================

Purpose
-------
This RUNBOOK documents how to run the AIOps prototype locally, how to troubleshoot common issues (venv activation, stuck port), and safety rules for Terraform/IaC (simulation-first).

Quick start (recommended)
-------------------------
From the repository root (Windows / Git Bash / PowerShell should all work):

1) Create venv, install runtime requirements, build frontend if present, and start backend+simulator in background:

```bash
python scripts/dev.py --quickstart --background
```

2) Check logs:

```bash
# Git Bash
tail -n 200 -f logs/backend.log
tail -n 200 -f logs/simulator.log

# PowerShell
Get-Content .\logs\backend.log -Tail 200 -Wait
Get-Content .\logs\simulator.log -Tail 200 -Wait
```

3) Inspect API data (example):

```bash
curl -sS http://127.0.0.1:8000/healthz
curl -sS http://127.0.0.1:8000/telemetry | jq '.[0:10]'
curl -sS http://127.0.0.1:8000/decisions | jq '.[0:10]'
```

Helpers
-------
- Create venv only:
  python scripts/dev.py --setup
- Install runtime requirements only:
  python scripts/dev.py --install
- Install development requirements (tests + lint):
  python scripts/dev.py --install-dev
- Run tests:
  python scripts/dev.py --run-tests
- Run lint (ruff + mypy):
  python scripts/dev.py --lint
- Start backend in foreground:
  python scripts/dev.py --start-backend
- Start simulator in background:
  python scripts/dev.py --start-simulator --sim-interval 2.5 --background

Troubleshooting
---------------
- "Permission denied" when creating `.venv`:
  - Ensure no antivirus is blocking file creation.
  - Try creating venv in a different folder or run in an elevated terminal.
- Activation confusion (Git Bash vs PowerShell):
  - You don't need to activate the venv when using `scripts/dev.py` — it runs the venv python directly.
  - If you want to activate manually: use `source .venv/Scripts/activate` (Git Bash) or `.\.venv\Scripts\Activate.ps1` (PowerShell).
- Port 8000 already in use / bind error:
  - Find process: `netstat -ano | findstr :8000`
  - Kill: `taskkill /PID <PID> /F`
  - Or pick another port by editing `scripts/dev.py` start command.
- Large number of TIME_WAIT entries: normal when many short-lived requests happen; not an error unless sockets are exhausted.

Safety notes (Terraform / cloud)
-------------------------------
- This repository is simulation-first. `infra/main.tf` uses a `simulate` flag by default; do NOT run `terraform apply` unless you have reviewed the plan and removed `simulate` intentionally.
- CI runs `terraform plan` on PRs (read `.github/workflows/terraform_plan.yml`). Manual apply is required for any real cloud change.

Next steps (recommended)
------------------------
- Run `python scripts/dev.py --install-dev` to install dev tools and then `python scripts/dev.py --run-tests` and `python scripts/dev.py --lint` to validate quality.
- Implement `RUNBOOK.md` additions for any infra or provider accounts when you decide to enable real cloud applies.
