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

resource "azurerm_search_service" "main" {
  name                          = "${var.project_name}-${var.environment}-search"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  sku                           = var.sku
  replica_count                 = var.replica_count
  partition_count               = var.partition_count
  semantic_search_sku           = "standard"
  local_authentication_enabled  = false
  authentication_failure_mode   = "http403"

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
