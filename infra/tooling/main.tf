provider "aws" {}

module "constants" {
  source = "../constants"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

module "aws_auditor" {
  source   = "./aws_auditor"
  prefix   = "${module.constants.prefix}audit_"
  auditors = jsondecode(file("auditors.json"))
  tags     = module.constants.common_tags
}