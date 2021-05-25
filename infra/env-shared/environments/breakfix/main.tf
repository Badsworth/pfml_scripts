# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh breakfix env-shared
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

locals {
  vpc = "nonprod"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-breakfix-env-mgmt"
    key            = "terraform/env-shared.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  environment_name  = "breakfix"
  nlb_name          = "${local.vpc}-nlb"
  nlb_vpc_link_name = "${local.vpc}-nlb-vpc-link"
  nlb_port          = 3504

  # AWS WAF ACL settings
  enable_regional_rate_based_acl = false
  enable_fortinet_managed_rules  = true
  enforce_fortinet_managed_rules = true # false = Count rule matches (override type = COUNT)
}                                        # true  = Block rule matches (override type = NONE)
