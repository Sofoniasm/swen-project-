#!/usr/bin/env bash
set -euo pipefail
# Run Terraform locally for infra/terraform using the same backend naming logic as the GitHub workflow.
# This script will call prepare-tf-backend.sh to ensure the S3 bucket and DDB lock exist, then init/apply.

if [ -z "${AWS_REGION:-}" ]; then
  echo "ERROR: AWS_REGION must be set (e.g. export AWS_REGION=us-east-1)" >&2
  exit 2
fi

ROOT_DIR=$(git rev-parse --show-toplevel)
cd "$ROOT_DIR/infra/terraform"

echo "Preparing backend resources (S3 bucket + DynamoDB)"
"$ROOT_DIR/scripts/prepare-tf-backend.sh"

if [ -z "${TF_STATE_BUCKET:-}" ] || [ -z "${TF_STATE_DDB_TABLE:-}" ]; then
  echo "After prepare-tf-backend.sh completes, ensure TF_STATE_BUCKET and TF_STATE_DDB_TABLE are exported in your shell." >&2
  echo "Example: export TF_STATE_BUCKET=...; export TF_STATE_DDB_TABLE=..." >&2
  # Try to continue: derive values from env if present
fi

echo "Initializing terraform with backend s3://${TF_STATE_BUCKET} (dynamodb table: ${TF_STATE_DDB_TABLE})"
terraform init -input=false \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=aiops/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${TF_STATE_DDB_TABLE}"

echo "Running terraform apply (this will create cloud resources and may cost money)."
read -r -p "Proceed with terraform apply? Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborting per user choice."; exit 0
fi

terraform apply -auto-approve

echo "Terraform apply finished. Run 'terraform output' to inspect outputs." 
