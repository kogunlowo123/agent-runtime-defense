output "cluster_id" {
  value       = azurerm_kubernetes_cluster.main.id
  description = "AKS cluster resource ID"
}

output "cluster_name" {
  value       = azurerm_kubernetes_cluster.main.name
  description = "AKS cluster name"
}

output "kube_config" {
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  description = "Raw kubeconfig for the cluster"
  sensitive   = true
}

output "host" {
  value       = azurerm_kubernetes_cluster.main.kube_config[0].host
  description = "Kubernetes API server host"
  sensitive   = true
}

output "cluster_ca_certificate" {
  value       = azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
  description = "Cluster CA certificate (base64)"
  sensitive   = true
}

output "oidc_issuer_url" {
  value       = azurerm_kubernetes_cluster.main.oidc_issuer_url
  description = "OIDC issuer URL for workload identity federation"
}

output "kubelet_identity" {
  value       = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  description = "Object ID of the kubelet managed identity"
}

output "log_analytics_workspace_id" {
  value       = azurerm_log_analytics_workspace.main.id
  description = "Log Analytics workspace resource ID"
}
