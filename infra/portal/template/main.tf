provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    archive = "~> 1.3"
    aws     = "~> 2.57"
  }
}

provider "newrelic" {
  version       = "~> 2.7.1"
  region        = "US"
  account_id    = local.newrelic_account_id
  api_key       = data.aws_ssm_parameter.newrelic-api-key.value
  admin_api_key = data.aws_ssm_parameter.newrelic-admin-api-key.value
}


data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

data "newrelic_entity" "pfml-portal" {
  # A reference to the Portal's top-level object in New Relic. Not managed by TF, but required by other Terraform objects.
  name   = "${upper(local.app_name)}-Portal-${upper(var.environment_name)}"
  domain = "BROWSER"
  type   = "APPLICATION"
}


locals {
  app_name                     = "pfml"
  newrelic_account_id          = "2837112" # PFML's New Relic sub-account number
  newrelic_trusted_account_key = "1606654" # EOLWD's New Relic parent account number
}

module "constants" {
  source = "../../constants"
}
