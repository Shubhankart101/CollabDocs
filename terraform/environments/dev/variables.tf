variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Django Secret Key"
  type        = string
  sensitive   = true
}
