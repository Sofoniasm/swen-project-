#!/usr/bin/env bash
set -euo pipefail

# Dispatch a GitHub Actions workflow via REST API and stream logs by downloading the run logs when complete.
# Usage: GITHUB_TOKEN=ghp_xxx ./scripts/dispatch-infra-api.sh [workflow-file] [ref]

WORKFLOW=${1:-terraform-apply.yml}
REF=${2:-main}
OWNER="Sofoniasm"
REPO="swen-project-"

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: GITHUB_TOKEN environment variable is not set. Create a PAT with 'repo' and 'workflow' scopes and export it as GITHUB_TOKEN." >&2
  exit 2
fi

AUTH_HEADER=( -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" )

echo "Dispatching workflow '$WORKFLOW' on ref '$REF' for $OWNER/$REPO..."
curl -s "${AUTH_HEADER[@]}" -X POST "https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches" -d "{\"ref\":\"${REF}\"}"

echo "Waiting for a run to be created..."
run_id=""
for i in {1..30}; do
  sleep 2
  out=$(curl -s "${AUTH_HEADER[@]}" "https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=10")
  run_id=$(python - <<PY
import sys,json,os
ref=os.environ['REF']
r=json.load(sys.stdin)
for run in r.get('workflow_runs',[]):
    if run.get('head_branch')==ref:
        print(run.get('id'))
        sys.exit(0)
sys.exit(1)
PY
  <<<"$out" 2>/dev/null || true)
  if [ -n "$run_id" ]; then
    echo "Found run id: $run_id"
    break
  fi
done

if [ -z "$run_id" ]; then
  echo "Failed to detect workflow run. Open Actions UI to inspect." >&2
  exit 3
fi

echo "Polling run status for run id $run_id..."
while true; do
  info=$(curl -s "${AUTH_HEADER[@]}" "https://api.github.com/repos/${OWNER}/${REPO}/actions/runs/${run_id}")
  status=$(python - <<PY
import sys,json
r=json.load(sys.stdin)
print(r.get('status'))
PY
  <<<"$info")
  conclusion=$(python - <<PY
import sys,json
r=json.load(sys.stdin)
print(r.get('conclusion'))
PY
  <<<"$info")
  echo "status=$status, conclusion=$conclusion"
  if [ "$status" = "completed" ]; then
    echo "Run completed with conclusion=$conclusion"
    break
  fi
  sleep 5
done

echo "Downloading run logs..."
tmpzip="/tmp/${REPO//./}-${run_id}-logs.zip"
curl -sL "${AUTH_HEADER[@]}" "https://api.github.com/repos/${OWNER}/${REPO}/actions/runs/${run_id}/logs" -o "$tmpzip"

if command -v unzip >/dev/null 2>&1; then
  tmpdir="/tmp/${REPO//./}-${run_id}-logs"
  rm -rf "$tmpdir" || true
  mkdir -p "$tmpdir"
  unzip -q "$tmpzip" -d "$tmpdir" || true
  echo "-- Logs extracted to $tmpdir --"
  # Print last 200 lines of each file
  for f in $(find "$tmpdir" -type f); do
    echo "===== $f ====="
    tail -n 200 "$f" || true
  done
else
  echo "Downloaded logs to $tmpzip (no 'unzip' available to extract). Open the file to inspect." >&2
fi

echo "Done."
