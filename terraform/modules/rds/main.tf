resource "aws_db_subnet_group" "main" {
  name       = "collabdocs-db-subnet-group-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "collabdocs-db-subnet-group-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "collabdocs-rds-sg-${var.environment}"
  description = "Security group for PostgreSQL RDS cluster"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL access from App SG"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "collabdocs-rds-sg-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_db_instance" "main" {
  identifier             = "collabdocs-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = var.environment == "dev" ? true : false
  multi_az               = var.multi_az

  tags = {
    Name        = "collabdocs-rds-${var.environment}"
    Environment = var.environment
  }
}
