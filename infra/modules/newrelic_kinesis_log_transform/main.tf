provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"
  required_providers {
    aws = "3.74.1"
  }
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

module "constants" {
  source = "../../constants"
}
