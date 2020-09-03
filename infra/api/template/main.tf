provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

provider "newrelic" {
  version       = "~> 2.0.0"
  region        = "US"
  account_id    = local.newrelic_account_id
  api_key       = data.aws_ssm_parameter.newrelic-api-key.value
  admin_api_key = data.aws_ssm_parameter.newrelic-admin-api-key.value
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

terraform {
  required_version = "0.12.24"
}

locals {
  app_name                     = "pfml-api"
  newrelic_account_id          = "2837112" # PFML's New Relic sub-account number
  newrelic_trusted_account_key = "1606654" # EOLWD's New Relic parent account number
}

module "constants" {
  source = "../../constants"
}
