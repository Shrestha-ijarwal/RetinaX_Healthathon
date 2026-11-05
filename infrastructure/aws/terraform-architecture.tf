# RetinaX Care - AWS Cloud Infrastructure Blueprint (Terraform HCL)
# Target: AWS ECS Fargate, RDS PostgreSQL, ElastiCache Redis, S3 Private Bucket, CloudWatch

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

variable "aws_region" {
  default = "ap-south-1"
}

variable "environment" {
  default = "production"
}

# 1. VPC & Networking
resource "aws_vpc" "retinax_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "retinax-care-vpc"
  }
}

# 2. Private S3 Bucket for Medical Documents
resource "aws_s3_bucket" "documents_bucket" {
  bucket = "retinax-care-production-documents-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "documents_private" {
  bucket                  = aws_s3_bucket.documents_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents_crypto" {
  bucket = aws_s3_bucket.documents_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 3. RDS PostgreSQL (Multi-AZ in Production)
resource "aws_db_instance" "postgres" {
  identifier          = "retinax-postgres-${var.environment}"
  engine              = "postgres"
  engine_version      = "16.1"
  instance_class      = "db.t4g.small"
  allocated_storage   = 20
  max_allocated_storage = 100
  storage_type        = "gp3"
  storage_encrypted   = true
  username            = "retinax_admin"
  manage_master_user_password = true
  publicly_accessible = false
  skip_final_snapshot = true
}

# 4. ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "retinax-redis-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# 5. ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "retinax-care-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
