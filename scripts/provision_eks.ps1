<#
.SYNOPSIS
  Provision a minimal EKS cluster and bootstrap cert-manager, ingress-nginx and ArgoCD on Windows (PowerShell).

.DESCRIPTION
  This script automates Terraform init/plan/apply, updates kubeconfig, installs cert-manager,
  ingress-nginx (LoadBalancer) and ArgoCD using Helm, applies the HTTP-01 ClusterIssuer and
  the ArgoCD Ingress manifest, and waits for the ingress LoadBalancer to become ready.

.USAGE
  Open PowerShell as a user with AWS CLI configured (aws configure). Then run:
    powershell -ExecutionPolicy Bypass -File .\scripts\provision_eks.ps1

  The script will prompt for confirmation before creating resources that can incur AWS charges.
#>

param(
    [string]$RepoRoot = (Get-Location).Path
)

function Check-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Required command '$name' not found on PATH. Please install and retry."
        exit 2
    }
}

Write-Host "Repository root: $RepoRoot"

# Required tools
foreach ($tool in @('terraform','aws','kubectl','helm')) {
    Check-Command $tool
}

# Safety prompt
Write-Host "WARNING: This script will create AWS resources (EKS cluster, EC2 nodes, LoadBalancer) which will incur charges." -ForegroundColor Yellow
$confirm = Read-Host "Type YES to continue, anything else to abort"
if ($confirm -ne 'YES') {
    Write-Host "Aborted by user. No changes made."
    exit 0
}

Push-Location (Join-Path $RepoRoot 'infra\terraform')
try {
    Write-Host "Running: terraform init -upgrade"
    & terraform init -upgrade

    Write-Host "Running: terraform plan -var-file=terraform.tfvars"
    & terraform plan -var-file=terraform.tfvars

    Write-Host "Running: terraform apply -auto-approve -var-file=terraform.tfvars"
    & terraform apply -auto-approve -var-file=terraform.tfvars

    Write-Host "Reading terraform outputs..."
    $clusterName = (& terraform output -raw cluster_name) -replace "\r|\n",""
    $awsRegion = (& terraform output -raw aws_region) -replace "\r|\n","" 2>$null
    if (-not $awsRegion) { $awsRegion = 'us-east-1' }
    Write-Host "Cluster: $clusterName  Region: $awsRegion"
}
catch {
    Write-Error "Terraform step failed: $_"
    Pop-Location
    exit 3
}
finally {
    Pop-Location
}

Write-Host "Updating kubeconfig for cluster $clusterName"
& aws eks update-kubeconfig --name $clusterName --region $awsRegion

Write-Host "Installing cert-manager (Helm)"
& helm repo add jetstack https://charts.jetstack.io 2>$null
& helm repo update
& helm upgrade --install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --version v1.11.0 --set installCRDs=true

Write-Host "Installing ingress-nginx (Helm) as LoadBalancer"
& helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>$null
& helm repo update
& helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace --set controller.replicaCount=1 --set controller.service.type=LoadBalancer

Write-Host "Waiting for ingress LoadBalancer external IP/hostname (this can take a few minutes)..."
$lbIp = $null; $lbHost = $null
for ($i=0; $i -lt 60; $i++) {
    try {
        $svc = & kubectl -n ingress-nginx get svc -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].status.loadBalancer.ingress[0]}' 2>$null
        if ($svc) {
            # svc may be like {"ip":"1.2.3.4"} or {"hostname":"..."}
            if ($svc -match '"ip"\s*:\s*"([^"]+)"') { $lbIp = $matches[1] }
            if ($svc -match '"hostname"\s*:\s*"([^"]+)"') { $lbHost = $matches[1] }
        }
    }
    catch { }
    if ($lbIp -or $lbHost) { break }
    Start-Sleep -Seconds 5
}

Write-Host "Installing ArgoCD (Helm, ClusterIP)"
& helm repo add argo https://argoproj.github.io/argo-helm 2>$null
& helm repo update
& helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace --set server.service.type=ClusterIP --set controller.replicas=1

Write-Host "Applying cert-manager HTTP-01 ClusterIssuer and ArgoCD Ingress (if present)"
$certIssuer = Join-Path $RepoRoot 'infra\cert-manager\cluster-issuer-http01.yaml'
if (Test-Path $certIssuer) { & kubectl apply -f $certIssuer } else { Write-Warning "ClusterIssuer manifest not found: $certIssuer" }

$argoIngress = Join-Path $RepoRoot 'infra\k8s\argocd-ingress.yaml'
if (Test-Path $argoIngress) { & kubectl apply -f $argoIngress } else { Write-Warning "ArgoCD ingress manifest not found: $argoIngress" }

Write-Host "--- Summary ---"
if ($lbIp) { Write-Host "Ingress LoadBalancer IP: $lbIp" } else { Write-Host "Ingress LoadBalancer Hostname: $lbHost" }
Write-Host "If your ArgoCD hostname in the ingress manifest is e.g. argocd.fidevops.xyz, create a DNS record in GoDaddy:
  - If IP: A record argocd -> $lbIp
  - If host: CNAME argocd -> $lbHost"

Write-Host "To destroy and stop costs run (PowerShell):" -ForegroundColor Yellow
Write-Host "  cd $RepoRoot\infra\terraform; terraform destroy -auto-approve -var-file=terraform.tfvars"

Write-Host "Done."
exit 0
