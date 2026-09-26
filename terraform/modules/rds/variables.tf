variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where RDS will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private Subnet IDs for RDS subnet group"
  type        = list(string)
}

variable "allocated_storage" {
  description = "Allocated storage size in GB"
  type        = number
  default     = 20
}

variable "instance_class" {
  description = "DB Instance Class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "collabdocs"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "collabuser"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "app_security_group_id" {
  description = "Application Security Group ID for ingress rules"
  type        = string
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}
