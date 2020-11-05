# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh training env-shared
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
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-training-env-mgmt"
    key            = "terraform/env-shared.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  # For non-custom domain names, we're relying on the API Gateway-provided URL
  # which prepends the "training" stage. This adds a header so Swagger UI knows
  # where to find UI files on the server.
  forwarded_path       = "'/training/api/'"
  enable_pretty_domain = false
  environment_name     = "training"
  nlb_name             = "${local.vpc}-nlb"
  nlb_vpc_link_name    = "${local.vpc}-nlb-vpc-link"
  nlb_port             = 3502
}
