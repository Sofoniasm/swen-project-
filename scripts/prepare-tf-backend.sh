#!/usr/bin/env bash
set -euo pipefail
# Prepare an S3 bucket and DynamoDB table for Terraform remote state locking.
# Usage: TF_STATE_BUCKET and AWS_REGION may be set in the environment.

echo "Preparing Terraform backend (S3 + DynamoDB)"

if [ -z "${AWS_REGION:-}" ]; then
  echo "ERROR: AWS_REGION must be set in the environment (e.g. export AWS_REGION=us-east-1)" >&2
  exit 2
fi

if [ -n "${TF_STATE_BUCKET:-}" ]; then
  BUCKET="$TF_STATE_BUCKET"
else
  ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
  REPO_LOWER=$(basename "$(git rev-parse --show-toplevel)" | tr '[:upper:]' '[:lower:]' || echo "repo")
  BUCKET="${REPO_LOWER}-aiops-terraform-state-${ACCOUNT}"
fi

if [ -n "${TF_STATE_DDB_TABLE:-}" ]; then
  DDB_TABLE="$TF_STATE_DDB_TABLE"
else
  DDB_TABLE="${BUCKET}-lock"
fi

echo "Using S3 bucket: ${BUCKET}"
echo "Using DynamoDB table: ${DDB_TABLE}"

# Create bucket if it doesn't exist
if aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
  echo "S3 bucket ${BUCKET} already exists"
else
  echo "Creating S3 bucket ${BUCKET} in region ${AWS_REGION}"
  if [ "${AWS_REGION}" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "${BUCKET}" --region "${AWS_REGION}"
  else
    aws s3api create-bucket --bucket "${BUCKET}" --region "${AWS_REGION}" --create-bucket-configuration LocationConstraint="${AWS_REGION}"
  fi
fi

# Create DynamoDB table if not exists
if aws dynamodb describe-table --table-name "${DDB_TABLE}" >/dev/null 2>&1; then
  echo "DynamoDB table ${DDB_TABLE} already exists"
else
  echo "Creating DynamoDB table ${DDB_TABLE} for Terraform state locking"
  aws dynamodb create-table --table-name "${DDB_TABLE}" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST --region "${AWS_REGION}"
  echo "Waiting for DynamoDB table to exist..."
  aws dynamodb wait table-exists --table-name "${DDB_TABLE}"
fi

echo "Backend resources are ready. Export the following environment variables for terraform init:"
echo "  export TF_STATE_BUCKET=${BUCKET}"
echo "  export TF_STATE_DDB_TABLE=${DDB_TABLE}"

echo "Done."
