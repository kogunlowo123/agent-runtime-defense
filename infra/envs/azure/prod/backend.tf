terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "ardterraformstate"
    container_name       = "tfstate"
    key                  = "prod/terraform.tfstate"
  }
}
