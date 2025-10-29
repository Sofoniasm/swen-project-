#!/usr/bin/env bash
set -euo pipefail
# Provision a minimal EKS cluster and bootstrap cert-manager, ingress-nginx and ArgoCD
# Usage: ./scripts/provision_eks.sh [path-to-repo-root]

REPO_ROOT="${1:-$(pwd)}"
TF_DIR="$REPO_ROOT/infra/terraform"
CERT_ISSUER_MANIFEST="$REPO_ROOT/infra/cert-manager/cluster-issuer-http01.yaml"
ARGOCD_INGRESS_MANIFEST="$REPO_ROOT/infra/k8s/argocd-ingress.yaml"

echo "Starting provisioning from repo root: $REPO_ROOT"

if ! command -v terraform &>/dev/null; then
  echo "terraform not found on PATH. Install terraform >= 1.3 and retry." >&2
  exit 2
fi
if ! command -v aws &>/dev/null; then
  echo "aws CLI not found on PATH. Install and configure credentials (aws configure)." >&2
  exit 2
fi
if ! command -v kubectl &>/dev/null; then
  echo "kubectl not found on PATH. Install kubectl compatible with k8s 1.27." >&2
  exit 2
fi
if ! command -v helm &>/dev/null; then
  echo "helm not found on PATH. Install helm v3+." >&2
  exit 2
fi

echo "1/8 - Initializing Terraform (will download pinned modules/providers)"
pushd "$TF_DIR" >/dev/null
terraform init -upgrade

echo "2/8 - Planning Terraform (showing changes)"
terraform plan -var-file=terraform.tfvars

echo "3/8 - Applying Terraform (this will create AWS resources and incur cost)"
terraform apply -auto-approve -var-file=terraform.tfvars

echo "4/8 - Read Terraform outputs"
CLUSTER_NAME=$(terraform output -raw cluster_name || true)
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || echo "${AWS_REGION:-us-east-1}")
popd >/dev/null

if [ -z "$CLUSTER_NAME" ]; then
  echo "ERROR: Could not read cluster_name from terraform outputs" >&2
  exit 3
fi

echo "5/8 - Updating kubeconfig for EKS cluster: $CLUSTER_NAME (region: $AWS_REGION)"
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION"

echo "6/8 - Installing cert-manager"
helm repo add jetstack https://charts.jetstack.io || true
helm repo update
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace --version v1.11.0 --set installCRDs=true

echo "7/8 - Installing ingress-nginx (LoadBalancer)"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx || true
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.replicaCount=1 \
  --set controller.service.type=LoadBalancer

echo "Waiting for ingress-nginx LoadBalancer external IP/hostname..."
for i in {1..60}; do
  LB_IP=$(kubectl -n ingress-nginx get svc -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
  LB_HOST=$(kubectl -n ingress-nginx get svc -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
  if [ -n "$LB_IP" ] || [ -n "$LB_HOST" ]; then
    echo "Found LoadBalancer: IP=$LB_IP HOST=$LB_HOST"
    break
  fi
  sleep 5
done

echo "8/8 - Installing ArgoCD (ClusterIP)"
helm repo add argo https://argoproj.github.io/argo-helm || true
helm repo update
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace \
  --set server.service.type=ClusterIP --set controller.replicas=1

echo "Applying cert-manager HTTP-01 ClusterIssuer and ArgoCD Ingress manifests"
kubectl apply -f "$CERT_ISSUER_MANIFEST" || true
kubectl apply -f "$ARGOCD_INGRESS_MANIFEST" || true

echo "Provisioning actions finished. Next steps:" 
echo " - If LB returned an IP, create an A record in your DNS for the ArgoCD hostname pointing to that IP." 
echo " - If LB returned a hostname, create a CNAME for that value." 
echo " - Update the ArgoCD ingress manifest's 'REPLACE_WITH_ARGOCD_HOSTNAME' to your desired host (e.g. argocd.fidevops.xyz) before applying for production." 
echo
echo "LoadBalancer result: IP=$LB_IP HOST=$LB_HOST"
echo "To destroy the cluster and stop costs:"
echo "  cd $TF_DIR && terraform destroy -auto-approve -var-file=terraform.tfvars"

exit 0
