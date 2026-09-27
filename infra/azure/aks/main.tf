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

# ---------------------------------------------------------------------------
# Log Analytics workspace for AKS monitoring
# ---------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-law"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 90
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# User-assigned managed identity for AKS
# ---------------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "aks" {
  name                = "${var.project_name}-${var.environment}-aks-identity"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# AKS cluster
# ---------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project_name}-${var.environment}-aks"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "system"
    vm_size             = var.node_vm_size
    node_count          = var.node_count
    enable_auto_scaling = true
    min_count           = var.min_node_count
    max_count           = var.max_node_count
    vnet_subnet_id      = var.vnet_subnet_id
    os_disk_size_gb     = 100
    type                = "VirtualMachineScaleSets"

    node_labels = {
      "node.kubernetes.io/pool" = "system"
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  azure_policy_enabled      = true
  workload_identity_enabled = true
  oidc_issuer_enabled       = true

  network_profile {
    network_plugin    = "azure"
    network_policy    = "calico"
    service_cidr      = "10.100.0.0/16"
    dns_service_ip    = "10.100.0.10"
    load_balancer_sku = "standard"
  }

  microsoft_defender {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [default_node_pool[0].node_count]
  }
}

# ---------------------------------------------------------------------------
# AcrPull role assignment so AKS can pull from ACR
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "aks_acr_pull" {
  count                = var.acr_id != "" ? 1 : 0
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

# ---------------------------------------------------------------------------
# Diagnostic settings — send AKS logs to Log Analytics
# ---------------------------------------------------------------------------

resource "azurerm_monitor_diagnostic_setting" "aks" {
  name                       = "${var.project_name}-${var.environment}-aks-diag"
  target_resource_id         = azurerm_kubernetes_cluster.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "kube-apiserver"
  }

  enabled_log {
    category = "kube-controller-manager"
  }

  enabled_log {
    category = "guard"
  }

  metric {
    category = "AllMetrics"
  }
}
