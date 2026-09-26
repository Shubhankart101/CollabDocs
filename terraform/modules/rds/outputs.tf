output "db_endpoint" {
  description = "Database connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_host" {
  description = "Database connection hostname"
  value       = aws_db_instance.main.address
}

output "db_port" {
  description = "Database connection port"
  value       = aws_db_instance.main.port
}

output "db_security_group_id" {
  description = "RDS Security Group ID"
  value       = aws_security_group.rds.id
}
