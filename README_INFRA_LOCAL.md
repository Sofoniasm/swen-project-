## Running the infra locally (developer-friendly)

This document explains how to run the infrastructure provisioning locally so a contributor who clones the repo can provision the EKS cluster and related resources.

Warning: running the infra will create cloud resources in your AWS account and may incur costs. Only run this if you have permissions and understand the cost implications.

Prerequisites
- Git clone of this repo
- AWS CLI configured (aws CLI v2) with credentials that have sufficient permissions to create IAM, EC2, EKS, S3, DynamoDB resources (or use an admin account for the dev environment).
- Terraform installed (>= 1.5.0 recommended)
- kubectl and helm (for post-apply bootstrapping)

Steps
1. Set environment variables (example):

```bash
export AWS_REGION=us-east-1
# optional: supply your own names
export TF_STATE_BUCKET=your-bucket-name
export TF_STATE_DDB_TABLE=your-table-name
```

2. Copy terraform example tfvars and edit if you want to reuse an existing VPC:

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
# edit infra/terraform/terraform.tfvars and set existing_vpc_id if you want to reuse a VPC
```

3. Prepare the Terraform backend (creates S3 bucket and DynamoDB lock table if needed):

```bash
./scripts/prepare-tf-backend.sh
# the script prints the TF_STATE_BUCKET and TF_STATE_DDB_TABLE values you may export
```

4. Run terraform init and apply via the convenience script:

```bash
./scripts/run-local-infra.sh
# follow prompts and type 'yes' to proceed with apply
```

5. After apply completes, you can check Terraform outputs and run the post-apply bootstrapping steps (kubectl/helm) as needed. The workflow `terraform-apply.yml` contains the same set of bootstrapping commands and can be used as a reference.

Troubleshooting & notes
- If you hit permission errors while creating IAM resources, ensure the AWS credentials you used have the required IAM permissions. The appropriate managed policy used by the CI is `infra/terraform/iam/terraform-iam-policy.json` — you can use it as a reference to grant the same permissions to your user for local runs.
- If you hit VPC quota issues, set `existing_vpc_id` in `infra/terraform/terraform.tfvars` to reuse an existing VPC.
- Clean up resources when done to avoid charges.
