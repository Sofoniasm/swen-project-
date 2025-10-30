param(
  [string]$Workflow = 'terraform-apply.yml',
  [string]$Ref = 'main'
)

$owner = 'Sofoniasm'
$repo = 'swen-project-'

if (-not $env:GITHUB_TOKEN) {
  Write-Error "GITHUB_TOKEN environment variable is not set. Create a PAT with 'repo' and 'workflow' scopes and set it as GITHUB_TOKEN."
  exit 2
}

$headers = @{ Authorization = "Bearer $($env:GITHUB_TOKEN)"; Accept = 'application/vnd.github+json' }

Write-Host "Dispatching workflow '$Workflow' on ref '$Ref' for $owner/$repo..."
try {
  $resp = Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$owner/$repo/actions/workflows/$Workflow/dispatches" -Headers $headers -Body (@{ref=$Ref} | ConvertTo-Json) -ErrorAction Stop
} catch {
  Write-Error "Failed to dispatch workflow. Response: $($_.Exception.Response.Content.ReadAsStringAsync().Result)"
  Write-Error "If the workflow lacks a 'workflow_dispatch' trigger add 'workflow_dispatch:' under 'on:' in the workflow YAML."
  exit 4
}

Write-Host "Waiting for run to be created..."
$runId = $null
for ($i=0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  $out = Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/$owner/$repo/actions/workflows/$Workflow/runs?per_page=10" -Headers $headers
  foreach ($run in $out.workflow_runs) {
    if ($run.head_branch -eq $Ref) { $runId = $run.id; break }
  }
  if ($runId) { break }
}

if (-not $runId) { Write-Error 'Failed to detect workflow run. Open Actions UI to inspect.'; exit 3 }

Write-Host "Found run id: $runId"
Write-Host "Polling run status..."
while ($true) {
  $info = Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/$owner/$repo/actions/runs/$runId" -Headers $headers
  $status = $info.status
  $conclusion = $info.conclusion
  Write-Host "status=$status, conclusion=$conclusion"
  if ($status -eq 'completed') { break }
  Start-Sleep -Seconds 5
}

Write-Host "Downloading run logs..."
$outZip = "$env:TEMP\${repo.TrimEnd('-')}_run_${runId}_logs.zip"
(Invoke-WebRequest -Uri "https://api.github.com/repos/$owner/$repo/actions/runs/$runId/logs" -Headers $headers -OutFile $outZip -UseBasicParsing) | Out-Null

if (Test-Path $outZip) {
  $extractDir = "$env:TEMP\${repo.TrimEnd('-')}_run_${runId}_logs"
  if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
  Expand-Archive -Path $outZip -DestinationPath $extractDir -Force
  Write-Host "Logs extracted to: $extractDir"
  Get-ChildItem -Path $extractDir -Recurse -File | ForEach-Object {
    Write-Host "===== $($_.FullName) ====="
    Get-Content -Path $_.FullName -Tail 200 -ErrorAction SilentlyContinue
  }
} else {
  Write-Error "Failed to download logs. File not found: $outZip"
}

Write-Host "Done."
