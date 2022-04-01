provider "aws" {}

module "constants" {
  source = "../constants"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

module "aws_auditor" {
  source         = "./aws_auditor"
  prefix         = "${module.constants.prefix}audit_"
  tags           = module.constants.common_tags
  region         = data.aws_region.current.name
  aws_account_id = data.aws_caller_identity.current.account_id
  schedule       = "rate(1 day)"
  // schedule       = "cron(0 6 * * ? *​)"
}