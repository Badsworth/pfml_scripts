# Management config for PagerDuty.
##
# This is not currently automated by Github Actions and is mostly meant to make setup faster
# for new projects or PagerDuty accounts.
#

# This key was generated by Kevin Yeh on 10-21-2020 and should be replaced if he leaves.
# This was manually stored in SSM and are not managed through Terraform.
# 
data "aws_ssm_parameter" "pagerduty_api_key" {
  name = "/admin/common/pagerduty-api-key"
}

provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

provider "newrelic" {
  version       = "~> 2.15.0"
  region        = "US"
  account_id    = "2837112"
  api_key       = data.aws_ssm_parameter.newrelic-api-key.value
  admin_api_key = data.aws_ssm_parameter.newrelic-admin-api-key.value
}

terraform {
  required_version = "0.13.6"

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    newrelic = {
      source = "newrelic/newrelic"
    }
    pagerduty = {
      source = "pagerduty/pagerduty"
    }
  }

  backend "s3" {
    bucket         = "massgov-pfml-aws-account-mgmt"
    key            = "terraform/monitoring.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    encrypt        = "true"
  }
}

provider "pagerduty" {
  token = data.aws_ssm_parameter.pagerduty_api_key.value
}

module "constants" {
  source = "../constants"
}
