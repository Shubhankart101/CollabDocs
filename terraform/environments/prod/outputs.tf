output "alb_url" {
  description = "Application Load Balancer URL"
  value       = "http://${module.app.alb_dns_name}"
}

output "db_endpoint" {
  description = "RDS Endpoint"
  value       = module.rds.db_endpoint
}
