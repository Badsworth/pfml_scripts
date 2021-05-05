# NOTE: This file is intended to be run within a temporary terraform workspace.
#
#   This is useful when you need to test changes to the resources in a dedicated
#   environment that won't be wiped out. The API Gateway will point to the API
#   in the test environment, although you can change this by switching the nlb_port
#   to whatever is configured in infra/api/environments/ENV/main.tf.
#
#   CORS might get in the way though.
#
#   Naming: do not use underscores, slashes, or other odd characters.
#
#   Usage:
#     terraform workspace new <your-helpful-name>
#     terraform plan / apply etc
#
#   Cleanup:
#     terraform destroy.
#     terraform workspace delete <your-helpful-name>
#
#   Listing all workspaces:
#     terraform workspace list
#
# ----
#
# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh adhoc env-shared
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
    bucket         = "massgov-pfml-adhoc-env-mgmt"
    key            = "terraform/env-shared.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  # Ensure that we're running in a dedicated workspace.
  # If not, this will error out during the plan step.
  environment_name   = terraform.workspace == "default" ? null : terraform.workspace
  is_adhoc_workspace = true

  nlb_name          = "${local.vpc}-nlb"
  nlb_vpc_link_name = "${local.vpc}-nlb-vpc-link"
  nlb_port          = 80

  # AWS WAF ACL settings
  enable_regional_rate_based_acl = true
  enable_fortinet_managed_rules  = true
  enforce_fortinet_managed_rules = false # false = Count rule matches (override type = COUNT)
}                                        # true  = Block rule matches (override type = NONE)

