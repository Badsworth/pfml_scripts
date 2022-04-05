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

module "aws_auditor" {
  source           = "./aws_auditor"
  prefix           = "${module.constants.prefix}audit_"
  tags             = module.constants.common_tags
  aws_region       = data.aws_region.current.name
  aws_account_id   = data.aws_caller_identity.current.account_id
  lambda_directory = "lambda_functions"
  schedule         = "rate(1 day)"
  // schedule       = "cron(0 6 * * ? *​)"
}