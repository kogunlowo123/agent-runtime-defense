variable "location" {
  type        = string
  description = "Azure region for all resources"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group to deploy into"
}

variable "project_name" {
  type        = string
  description = "Short project name used in resource naming"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version for the AKS cluster"
  default     = "1.29"
}

variable "node_vm_size" {
  type        = string
  description = "VM size for default node pool"
  default     = "Standard_D4ds_v5"
}

variable "node_count" {
  type        = number
  description = "Initial node count"
  default     = 3
}

variable "min_node_count" {
  type        = number
  description = "Minimum node count for autoscaling"
  default     = 2
}

variable "max_node_count" {
  type        = number
  description = "Maximum node count for autoscaling"
  default     = 10
}

variable "dns_prefix" {
  type        = string
  description = "DNS prefix for the AKS cluster"
}

variable "vnet_subnet_id" {
  type        = string
  description = "Subnet ID for AKS nodes"
}

variable "acr_id" {
  type        = string
  description = "Azure Container Registry resource ID (for AcrPull assignment)"
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default     = {}
}
