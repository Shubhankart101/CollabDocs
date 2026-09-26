terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source              = "../../modules/vpc"
  environment         = var.environment
  vpc_cidr            = "10.1.0.0/16"
  public_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24"]
}

module "app" {
  source             = "../../modules/app"
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  db_host            = module.rds.db_host
  db_name            = "collabdocs_prod"
  db_username        = "collabuser_prod"
  db_password        = var.db_password
  secret_key         = var.secret_key
  desired_count      = 4
  cpu                = 512
  memory             = 1024
}

module "rds" {
  source                = "../../modules/rds"
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.app.app_security_group_id
  instance_class        = "db.t3.medium"
  allocated_storage     = 100
  db_name               = "collabdocs_prod"
  db_username           = "collabuser_prod"
  db_password           = var.db_password
  multi_az              = true
}
