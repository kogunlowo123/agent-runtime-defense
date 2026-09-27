output "vnet_id" { value = azurerm_virtual_network.main.id }
output "vnet_name" { value = azurerm_virtual_network.main.name }
output "aks_subnet_id" { value = azurerm_subnet.aks.id }
output "postgres_subnet_id" { value = azurerm_subnet.postgres.id }
output "private_endpoints_subnet_id" { value = azurerm_subnet.private_endpoints.id }
output "resource_group_name" { value = azurerm_resource_group.network.name }
output "postgres_private_dns_zone_id" { value = azurerm_private_dns_zone.postgres.id }
output "keyvault_private_dns_zone_id" { value = azurerm_private_dns_zone.keyvault.id }
