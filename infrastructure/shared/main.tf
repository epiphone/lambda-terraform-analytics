terraform {
  backend "s3" {
    encrypt = true
    bucket  = "tacit-terraform-state-shared"
    key     = "terraform.tfstate"
    region  = "eu-central-1"
  }
}

provider "aws" {
  region = "eu-central-1"
}

resource "aws_s3_bucket" "terraform-state-storage-s3" {
  bucket = "tacit-terraform-state-shared"

  versioning {
    enabled = true
  }

  tags = {
    Name = "S3 Terraform remote state store for shared environment"
  }
}

resource "aws_security_group" "allow_postgres_from_all" {
  name        = "allow_postgres_from_all"
  description = "Allow Postgres access from everywhere"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "shared_analytics_db" {
  identifier              = "shared-analytics-db"
  allocated_storage       = 20
  storage_type            = "gp2"
  engine                  = "postgres"
  engine_version          = "9.6.5"
  instance_class          = "db.t2.micro"
  name                    = "analytics_db"
  username                = "${var.analytics_db_master_username}"
  password                = "${var.analytics_db_master_password}"
  port                    = 5432
  publicly_accessible     = true
  backup_retention_period = 7
  vpc_security_group_ids  = ["${aws_security_group.allow_postgres_from_all.id}"]
}
