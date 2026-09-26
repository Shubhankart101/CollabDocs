output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "app_security_group_id" {
  description = "Application Security Group ID"
  value       = aws_security_group.app.id
}
