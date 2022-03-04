provider "aws" {
  region = "us-east-1"
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

terraform {
  required_version = "0.14.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.74.1"
    }
    newrelic = {
      source = "newrelic/newrelic"
    }
    pagerduty = {
      source = "pagerduty/pagerduty"
    }
  }
}

locals {
  app_name = "pfml-api"
}

module "constants" {
  source = "../../constants"
}

# Defined in pfml-aws/kms.tf
data "aws_kms_key" "env_kms_key" {
  key_id = "alias/massgov-pfml-${var.environment_name}-kms-key"
}