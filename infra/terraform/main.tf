terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # Pin to the 4.x series so modules expecting older aws provider arguments
      # (used by some v3.x of the VPC module) remain compatible.
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = false
  single_nat_gateway = false

  tags = var.tags
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  # Pin to v18.x which accepts the legacy inputs used below (create_vpc, node_groups).
  # v19 introduced input changes; pinning keeps the existing config working.
  version         = "~> 18.0"

  cluster_name    = var.cluster_name
  # Use the configurable EKS Kubernetes version. Default is set in variables.tf.
  cluster_version = var.cluster_version

  # Provide the created VPC/subnets to the EKS module
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Minimal managed node group (single small instance to reduce cost)
  eks_managed_node_groups = {
    minimal = {
      desired_size   = var.node_count
      min_size       = 1
      max_size       = 1
      instance_types = [var.instance_type]
    }
  }

  tags = var.tags
}
