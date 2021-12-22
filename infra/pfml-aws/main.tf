provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-aws-account-mgmt"
    key            = "terraform/aws.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    encrypt        = "true"
  }
}

data "aws_region" "current" {
}


data "aws_caller_identity" "current" {
}

module "constants" {
  source = "../constants"
}