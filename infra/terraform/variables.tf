variable "aws_region" {
  description = "AWS region to create resources in"
  type        = string
  default     = "us-east-1"
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
