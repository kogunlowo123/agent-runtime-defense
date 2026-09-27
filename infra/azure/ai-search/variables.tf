variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "sku" { type = string; default = "standard" }
variable "replica_count" { type = number; default = 1 }
variable "partition_count" { type = number; default = 1 }
variable "tags" { type = map(string); default = {} }
