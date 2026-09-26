# CollabDocs Modular Terraform Infrastructure Guide

This document details the modular Infrastructure-as-Code (IaC) setup for **CollabDocs** using **Terraform (v1.5+)** to provision production-grade AWS cloud infrastructure.

---

## 🏛 AWS Architecture Diagram

```text
                                +-----------------------------------+
                                |          Internet Traffic         |
                                +-----------------+-----------------+
                                                  |
                                                  v
                                +-----------------------------------+
                                |    AWS Internet Gateway (IGW)     |
                                +-----------------+-----------------+
                                                  |
                                                  v
    +-----------------------------------------------------------------------------------+
    | PUBLIC SUBNETS (10.x.1.0/24, 10.x.2.0/24)                                         |
    |                                                                                   |
    |   +---------------------------------+        +--------------------------------+  |
    |   | Application Load Balancer (ALB) |        |       NAT Gateway (EIP)        |  |
    |   +----------------+----------------+        +----------------+---------------+  |
    +--------------------|------------------------------------------|-------------------+
                         |                                          |
                         v                                          v
    +--------------------|------------------------------------------|-------------------+
    | PRIVATE SUBNETS (10.x.10.0/24, 10.x.11.0/24)                          |  |
    |                    |                                          |                   |
    |   +----------------v----------------+                         |                   |
    |   |   ECS Fargate Tasks (App SG)    |-------------------------+                   |
    |   +----------------+----------------+ (Outbound Internet via NAT)                 |
    |                    |                                                              |
    |                    v Port 5432 (Ingress restricted to App SG)                     |
    |   +----------------+----------------+                                             |
    |   | PostgreSQL RDS (Multi-AZ / SG)  |                                             |
    |   +---------------------------------+                                             |
    +-----------------------------------------------------------------------------------+
```

---

## 📁 Directory & Module Structure

```text
terraform/
├── modules/
│   ├── vpc/                         # Virtual Private Cloud, Subnets & Routing
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/                         # Amazon RDS PostgreSQL Database Cluster
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── app/                         # ECS Fargate, Task Definitions & ALB
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/                         # Single-AZ development environment
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars.example
    └── prod/                        # High-Availability Multi-AZ production environment
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars.example
```

---

## 📦 Module Deep Dive

### 1. `vpc` Module (`terraform/modules/vpc/`)

- **Resources Provisioned**:
  - `aws_vpc.main`: Primary VPC with DNS hostnames and DNS support enabled.
  - `aws_internet_gateway.igw`: Internet Gateway attached to VPC.
  - `aws_subnet.public[*]`: Public subnets mapping public IPs on launch across 2 Availability Zones.
  - `aws_subnet.private[*]`: Private subnets isolated from direct internet access.
  - `aws_eip.nat`: Elastic IP assigned to the NAT Gateway.
  - `aws_nat_gateway.nat`: NAT Gateway in public subnet enabling outbound internet access for private subnet ECS tasks.
  - `aws_route_table.public` & `aws_route_table.private`: Route tables routing public traffic via IGW and private outbound traffic via NAT.
- **Key Outputs**: `vpc_id`, `public_subnet_ids`, `private_subnet_ids`.

---

### 2. `rds` Module (`terraform/modules/rds/`)

- **Resources Provisioned**:
  - `aws_db_subnet_group.main`: Associates private subnets for RDS deployment.
  - `aws_security_group.rds`: Database security group restricting port 5432 access strictly to `app_security_group_id`.
  - `aws_db_instance.main`: PostgreSQL 15.4 DB instance configured with storage, username, password, multi-AZ flags, and snapshot retention.
- **Key Outputs**: `db_endpoint`, `db_host`, `db_port`, `db_security_group_id`.

---

### 3. `app` Module (`terraform/modules/app/`)

- **Resources Provisioned**:
  - `aws_security_group.alb`: Security group accepting HTTP (80) / HTTPS (443) from public internet (`0.0.0.0/0`).
  - `aws_security_group.app`: Security group allowing container port ingress strictly from `alb` security group.
  - `aws_lb.main`: Application Load Balancer in public subnets.
  - `aws_lb_target_group.main`: Target group pointing to ECS tasks on port 8000 with health checks (`GET /api/`).
  - `aws_lb_listener.http`: Listens on HTTP port 80 and forwards to target group.
  - `aws_ecs_cluster.main`: ECS Cluster managing Fargate task execution.
  - `aws_ecs_task_definition.app`: Fargate task spec passing environment variables (`SECRET_KEY`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
  - `aws_ecs_service.app`: Fargate service enforcing `desired_count` across private subnets.
- **Key Outputs**: `alb_dns_name`, `app_security_group_id`.

---

## 📊 Environment Parameter Matrix (`dev` vs `prod`)

| Parameter | Development (`dev`) | Production (`prod`) |
| :--- | :--- | :--- |
| **VPC CIDR** | `10.0.0.0/16` | `10.1.0.0/16` |
| **Public Subnet CIDRs** | `10.0.1.0/24`, `10.0.2.0/24` | `10.1.1.0/24`, `10.1.2.0/24` |
| **Private Subnet CIDRs** | `10.0.10.0/24`, `10.0.11.0/24` | `10.1.10.0/24`, `10.1.11.0/24` |
| **ECS Task CPU** | `256` (0.25 vCPU) | `512` (0.5 vCPU) |
| **ECS Task Memory** | `512 MB` | `1024 MB` |
| **ECS Desired Task Count** | `1` | `4` |
| **RDS DB Instance Class** | `db.t3.micro` | `db.t3.medium` |
| **RDS Storage Size** | `20 GB` | `100 GB` |
| **RDS Multi-AZ Deployment** | `false` (Cost optimized) | `true` (High Availability) |
| **RDS Skip Final Snapshot** | `true` | `false` |

---

## 🚀 Step-by-Step Operations Guide

### 1. Initialize & Provision Development Environment

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with secure credentials
# db_password = "your-secure-dev-db-pass"
# secret_key  = "your-django-dev-secret-key"

terraform init
terraform plan
terraform apply -auto-approve
```

### 2. Initialize & Provision Production Environment

```bash
cd terraform/environments/prod
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with production secrets
terraform init
terraform plan
terraform apply -auto-approve
```

### 3. Teardown Environment

```bash
cd terraform/environments/dev
terraform destroy -auto-approve
```
