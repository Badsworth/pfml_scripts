provider "aws" {}

terraform {
  backend "s3" {
    bucket         = "massgov-pfml-aws-account-mgmt"
    key            = "terraform/infra-tooling.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    encrypt        = "true"
  }
}

module "constants" {
  source = "../constants"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}