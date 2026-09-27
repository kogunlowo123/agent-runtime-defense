module "network" {
  source              = "../../azure/network"
  location            = var.location
  resource_group_name = "${var.project_name}-${var.environment}-rg"
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
}

module "aks" {
  source              = "../../azure/aks"
  location            = var.location
  resource_group_name = module.network.resource_group_name
  project_name        = var.project_name
  environment         = var.environment
  dns_prefix          = "${var.project_name}-${var.environment}"
  vnet_subnet_id      = module.network.aks_subnet_id
  node_vm_size        = "Standard_D8ds_v5"
  node_count          = 5
  min_node_count      = 3
  max_node_count      = 20
  tags                = local.common_tags
}

module "postgres" {
  source                 = "../../azure/postgres-flex"
  location               = var.location
  resource_group_name    = module.network.resource_group_name
  project_name           = var.project_name
  environment            = var.environment
  sku_name               = "GP_Standard_D4s_v3"
  storage_mb             = 131072
  delegated_subnet_id    = module.network.postgres_subnet_id
  private_dns_zone_id    = module.network.postgres_private_dns_zone_id
  administrator_login    = var.db_admin_login
  administrator_password = var.db_admin_password
  tags                   = local.common_tags
}

module "monitor" {
  source              = "../../azure/monitor"
  location            = var.location
  resource_group_name = module.network.resource_group_name
  project_name        = var.project_name
  environment         = var.environment
  alert_email         = var.alert_email
  tags                = local.common_tags
}

module "keyvault" {
  source                     = "../../azure/keyvault"
  location                   = var.location
  resource_group_name        = module.network.resource_group_name
  project_name               = var.project_name
  environment                = var.environment
  log_analytics_workspace_id = module.monitor.log_analytics_workspace_id
  tags                       = local.common_tags
}

module "servicebus" {
  source              = "../../azure/servicebus"
  location            = var.location
  resource_group_name = module.network.resource_group_name
  project_name        = var.project_name
  environment         = var.environment
  tags                = local.common_tags
}

locals {
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    criticality = "production"
  }
}
