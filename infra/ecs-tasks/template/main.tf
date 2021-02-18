provider "aws" {
  region = "us-east-1"
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
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
}

locals {
  app_name = "pfml-api"
}

module "constants" {
  source = "../../constants"
}
