terraform {
  required_version = "0.12.24"

  required_providers {
    aws      = "~> 3.13.0"
    random   = "~> 3.0.0"
    template = "~> 2.2.0"
  }
}

provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
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

data "newrelic_entity" "pfml-api" {
  # A reference to the API's top-level object in New Relic. Not managed by TF, but required by other Terraform objects.
  name   = "${upper(local.app_name)}-${upper(var.environment_name)}"
  domain = "APM"
  type   = "APPLICATION"
}

locals {
  app_name                     = "pfml-api"
  newrelic_account_id          = "2837112" # PFML's New Relic sub-account number
  newrelic_trusted_account_key = "1606654" # EOLWD's New Relic parent account number
}

module "constants" {
  source = "../../constants"
}

data "terraform_remote_state" "pagerduty" {
  backend = "s3"

  config = {
    bucket = "massgov-pfml-aws-account-mgmt"
    key    = "terraform/pagerduty.tfstate"
    region = "us-east-1"
  }
}
