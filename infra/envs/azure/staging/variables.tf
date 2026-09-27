variable "project_name" { type = string; default = "ard" }
variable "environment" { type = string; default = "staging" }
variable "location" { type = string; default = "eastus2" }
variable "db_admin_login" { type = string; default = "ard_admin" }
variable "db_admin_password" { type = string; sensitive = true }
variable "alert_email" { type = string; default = "alerts@example.com" }
