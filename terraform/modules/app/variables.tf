variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public Subnet IDs for ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private Subnet IDs for ECS tasks"
  type        = list(string)
}

variable "app_image" {
  description = "Docker image for CollabDocs API"
  type        = string
  default     = "collabdocs-api:latest"
}

variable "container_port" {
  description = "Container application port"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 512
}

variable "db_host" {
  description = "PostgreSQL DB Host"
  type        = string
}

variable "db_name" {
  description = "PostgreSQL DB Name"
  type        = string
}

variable "db_username" {
  description = "PostgreSQL DB User"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL DB Password"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Django Secret Key"
  type        = string
  sensitive   = true
}
