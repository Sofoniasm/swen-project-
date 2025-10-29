#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Create a minimal EKS cluster using eksctl and bootstrap cert-manager, ingress-nginx and ArgoCD on Windows (PowerShell).

.DESCRIPTION
  This script uses eksctl to create a small EKS cluster (1 t3.small node), then installs cert-manager,
  ingress-nginx (LoadBalancer) and ArgoCD using Helm, applies the HTTP-01 ClusterIssuer and
  the ArgoCD Ingress manifest (it will replace the hostname placeholder if provided).

.PARAMETER HostName
  The DNS name to use for ArgoCD ingress (e.g. argocd.fidevops.xyz). If provided the script will
  update `infra/k8s/argocd-ingress.yaml` to use that host before applying it.

.USAGE
  powershell -ExecutionPolicy Bypass -File .\scripts\provision_eks_eksctl.ps1 -HostName argocd.fidevops.xyz
#>

param(
  [string]$HostName = 'argocd.fidevops.xyz',
  [string]$ClusterName = 'aiops-eks-cluster',
  [string]$Region = 'us-east-1',
  [string]$NodeType = 't3.small',
  [int]$Nodes = 1
)

function Check-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Required command '$name' not found on PATH. Please install and retry."
        exit 2
    }
}

foreach ($tool in @('eksctl','aws','kubectl','helm')) { Check-Command $tool }

Write-Host "This will create an EKS cluster named '$ClusterName' in $Region with $Nodes x $NodeType nodes." -ForegroundColor Yellow
$confirm = Read-Host "Type YES to continue, anything else to abort"
if ($confirm -ne 'YES') { Write-Host "Aborted."; exit 0 }

Write-Host "Creating EKS cluster with eksctl (may take ~10-15 minutes)"
& eksctl create cluster --name $ClusterName --region $Region --nodes $Nodes --node-type $NodeType --nodegroup-name ng-minimal --managed

Write-Host "Cluster created (eksctl updates kubeconfig). Waiting for nodes to be ready..."
for ($i=0; $i -lt 60; $i++) {
  $nodes = (& kubectl get nodes --no-headers 2>$null) -join "`n"
  if ($nodes -and ($nodes -match 'Ready')) { break }
  Start-Sleep -Seconds 10
}

Write-Host "Installing cert-manager"
helm repo add jetstack https://charts.jetstack.io 2>$null
helm repo update
helm upgrade --install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --version v1.11.0 --set installCRDs=true

Write-Host "Installing ingress-nginx (LoadBalancer)"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>$null
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace --set controller.replicaCount=1 --set controller.service.type=LoadBalancer

Write-Host "Installing ArgoCD (ClusterIP)"
helm repo add argo https://argoproj.github.io/argo-helm 2>$null
helm repo update
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace --set server.service.type=ClusterIP --set controller.replicas=1

# Replace ingress host placeholder if file exists
$ingressFile = Join-Path $PSScriptRoot '..\infra\k8s\argocd-ingress.yaml' | Resolve-Path -ErrorAction SilentlyContinue
if ($ingressFile) {
  $path = $ingressFile.Path
  (Get-Content $path) -replace 'REPLACE_WITH_ARGOCD_HOSTNAME', $HostName | Set-Content $path
  Write-Host "Replaced placeholder in $path with host $HostName"
}

Write-Host "Applying cert-manager HTTP-01 ClusterIssuer and ArgoCD Ingress"
$certIssuer = Join-Path $PSScriptRoot '..\infra\cert-manager\cluster-issuer-http01.yaml'
if (Test-Path $certIssuer) { & kubectl apply -f $certIssuer } else { Write-Warning "Missing $certIssuer" }

$ingressPath = Join-Path $PSScriptRoot '..\infra\k8s\argocd-ingress.yaml'
if (Test-Path $ingressPath) { & kubectl apply -f $ingressPath } else { Write-Warning "Missing $ingressPath" }

Write-Host "Waiting for LoadBalancer external IP/hostname..."
$LB_IP = $null; $LB_HOST = $null
for ($i=0; $i -lt 60; $i++) {
  $LB_IP = (& kubectl -n ingress-nginx get svc -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>$null)
  $LB_HOST = (& kubectl -n ingress-nginx get svc -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>$null)
  if ($LB_IP -or $LB_HOST) { break }
  Start-Sleep -Seconds 10
}

Write-Host "Provisioning done. LoadBalancer info:" -ForegroundColor Green
if ($LB_IP) { Write-Host "LB IP: $LB_IP" } else { Write-Host "LB Hostname: $LB_HOST" }
Write-Host "Next: create a DNS record in GoDaddy pointing $HostName to the LB IP/CNAME and wait for cert-manager to issue the TLS certificate."
Write-Host "To delete the cluster later: eksctl delete cluster --name $ClusterName --region $Region"

exit 0
