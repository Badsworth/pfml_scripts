provider "aws" {}

module "constants" {
  source = "../../constants"
}

module "aws_auditors" {
    source = "aws_auditors"
    prefix   = "${module.constants.prefix}audit_"
    auditors = jsondecode(file("auditors.json"))
    tags = module.constants.common_tags
}



locals {
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
