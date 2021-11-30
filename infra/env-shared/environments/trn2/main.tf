# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh trn2 env-shared
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

locals {
  vpc = "trn2" == "prod" ? "prod" : "nonprod"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-trn2-env-mgmt"
    key            = "terraform/env-shared.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  environment_name     = "trn2"
  nlb_name             = "${local.vpc}-nlb"
  nlb_vpc_link_name    = "${local.vpc}-nlb-vpc-link"
  nlb_port             = 3508

  # AWS WAF ACL settings
  enable_regional_rate_based_acl = true
  enable_fortinet_managed_rules  = false
}
