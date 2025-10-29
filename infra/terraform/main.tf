terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.27"

  # Create a minimal VPC for the cluster (default settings).
  create_vpc = true

  # Minimal managed node group (single small instance to reduce cost)
  node_groups = {
    minimal = {
      desired_capacity = var.node_count
      min_capacity     = 1
      max_capacity     = 1
      instance_types   = [var.instance_type]
    }
  }

  tags = var.tags
}
