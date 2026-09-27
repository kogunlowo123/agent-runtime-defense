variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "alert_email" {
  type    = string
  default = "alerts@example.com"
}
variable "tags" {
  type    = map(string)
  default = {}
}
