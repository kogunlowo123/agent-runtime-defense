variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "log_analytics_workspace_id" { type = string }
variable "allowed_ip_ranges" {
  type    = list(string)
  default = []
}
variable "tags" {
  type    = map(string)
  default = {}
}
