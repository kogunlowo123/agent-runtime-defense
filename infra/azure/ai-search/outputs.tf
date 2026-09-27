output "search_service_id" { value = azurerm_search_service.main.id }
output "search_service_name" { value = azurerm_search_service.main.name }
output "primary_key" {
  value     = azurerm_search_service.main.primary_key
  sensitive = true
}
