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

resource "azurerm_servicebus_namespace" "main" {
  name                          = "${var.project_name}-${var.environment}-sb"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  sku                           = "Premium"
  capacity                      = 1
  premium_messaging_partitions  = 1
  zone_redundant                = var.environment == "prod"
  local_auth_enabled            = false

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_servicebus_queue" "anomaly_detected" {
  name         = "anomaly-detected"
  namespace_id = azurerm_servicebus_namespace.main.id

  max_size_in_megabytes                 = 5120
  lock_duration                         = "PT1M"
  max_delivery_count                    = 10
  dead_lettering_on_message_expiration  = true
  requires_duplicate_detection          = true
  duplicate_detection_history_time_window = "PT10M"
  default_message_ttl                   = "P7D"
}

resource "azurerm_servicebus_queue" "response_executed" {
  name         = "response-executed"
  namespace_id = azurerm_servicebus_namespace.main.id

  max_size_in_megabytes        = 1024
  lock_duration                = "PT30S"
  max_delivery_count           = 5
  dead_lettering_on_message_expiration = true
  default_message_ttl          = "P3D"
}

resource "azurerm_servicebus_queue" "threat_signal" {
  name         = "threat-signal"
  namespace_id = azurerm_servicebus_namespace.main.id

  max_size_in_megabytes        = 5120
  lock_duration                = "PT1M"
  max_delivery_count           = 10
  dead_lettering_on_message_expiration = true
  default_message_ttl          = "P14D"
}

resource "azurerm_servicebus_namespace_authorization_rule" "api_send_listen" {
  name         = "api-send-listen"
  namespace_id = azurerm_servicebus_namespace.main.id
  listen       = true
  send         = true
  manage       = false
}
