variable "aws_region" {
  description = "AWS region to create resources in"
  type        = string
  default     = "us-east-1"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster (must be supported in the target region)"
  type        = string
  # Set to the latest supported EKS version observed in your account/region.
  # Updated to 1.34 (latest available per account query).
  default     = "1.34"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "aiops-eks-cluster"
}

variable "instance_type" {
  description = "EC2 instance type for node group (keep small to reduce cost)"
  type        = string
  default     = "t3.small"
}

variable "node_count" {
  description = "Desired number of nodes in the managed node group"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {
    "ManagedBy" = "terraform"
    "Project"   = "aiops"
  }
}
