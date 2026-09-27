terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
  required_version = ">= 1.7"
}

provider "azurerm" {
  features {}
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-law"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 90
  daily_quota_gb      = 10
  tags                = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-${var.environment}-appinsights"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = var.tags
}

resource "azurerm_monitor_action_group" "critical" {
  name                = "${var.project_name}-${var.environment}-critical-ag"
  resource_group_name = var.resource_group_name
  short_name          = "ard-critical"

  email_receiver {
    name          = "platform-team"
    email_address = var.alert_email
  }
}

resource "azurerm_security_insights_sentinel_onboarding" "main" {
  workspace_id              = azurerm_log_analytics_workspace.main.id
  customer_managed_key_enabled = false
}
