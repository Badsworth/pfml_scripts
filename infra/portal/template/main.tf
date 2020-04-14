provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    archive = "~> 1.3"
    aws     = "~> 2.57"
  }
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

locals {
  app_name = "pfml"
}
