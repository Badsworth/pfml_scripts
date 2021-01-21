# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh stage env-shared
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

locals {
  vpc = "stage" == "prod" ? "prod" : "nonprod"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-stage-env-mgmt"
    key            = "terraform/env-shared.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  environment_name  = "stage"
  nlb_name          = "${local.vpc}-nlb"
  nlb_vpc_link_name = "${local.vpc}-nlb-vpc-link"
  nlb_port          = 3500

  # AWS WAF ACL settings
  enable_regional_rate_based_acl = true
  enable_fortinet_managed_rules  = true
  enforce_fortinet_managed_rules = false # false = Count rule matches (override type = COUNT)
}                                        # true  = Block rule matches (override type = NONE)