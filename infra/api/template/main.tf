provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

terraform {
  required_version = "0.12.24"
}

locals {
  app_name = "pfml-api"
}

module "constants" {
  source = "../../constants"
}

