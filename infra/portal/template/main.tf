provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    archive = "~> 1.3"
    aws     = "~> 3.56.0"
    newrelic = {
      source = "newrelic/newrelic"
    }
  }
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

locals {
  app_name                     = "pfml"
  newrelic_account_id          = "2837112" # PFML's New Relic sub-account number
  newrelic_trusted_account_key = "1606654" # EOLWD's New Relic parent account number
}

provider "newrelic" {
  version       = "~> 2.15.0"
  region        = "US"
  account_id    = "2837112"
  api_key       = data.aws_ssm_parameter.newrelic-api-key.value
  admin_api_key = data.aws_ssm_parameter.newrelic-admin-api-key.value
}

module "constants" {
  source = "../../constants"
}

data "aws_ssm_parameter" "newrelic-api-key" {
  name = "/admin/pfml-api/newrelic-api-key"
}

data "aws_ssm_parameter" "newrelic-admin-api-key" {
  name = "/admin/pfml-api/newrelic-admin-api-key"
}