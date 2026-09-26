# CollabDocs Terraform Infrastructure

CollabDocs utilizes modular Infrastructure-as-Code (IaC) with **Terraform** to provision cloud infrastructure on AWS.

---

## 🏛 Directory Structure

```text
terraform/
├── modules/
│   ├── vpc/                         # Virtual Private Cloud module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/                         # Managed PostgreSQL Database module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── app/                         # ECS / Fargate Application module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/                         # Development environment configuration
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars.example
    └── prod/                        # Production environment configuration
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars.example
```

---

## 📦 Infrastructure Modules

### 1. `vpc` Module

- Provisions AWS VPC, Internet Gateway, public/private subnets across multiple availability zones, NAT Gateways, and route tables.

### 2. `rds` Module

- Provisions PostgreSQL Amazon RDS database instances within private subnets.
- Configures security groups restricting database access strictly to the application security group.
- Supports single-AZ for dev and Multi-AZ replication for production.

### 3. `app` Module

- Provisions AWS ECS (Elastic Container Service) with Fargate launch type, Task Definitions, and Application Load Balancers (ALB) for SSL termination and traffic routing.

---

## 🚀 Deployment Instructions

### Deploying Development Environment

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Update credentials in terraform.tfvars
terraform init
terraform plan
terraform apply
```

### Deploying Production Environment

```bash
cd terraform/environments/prod
cp terraform.tfvars.example terraform.tfvars
# Update production credentials in terraform.tfvars
terraform init
terraform plan
terraform apply
```
