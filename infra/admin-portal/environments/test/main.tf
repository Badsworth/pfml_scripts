# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh test portal
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/admin-portal.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "massgov_pfml" {
  # You probably don't need to change the variables below:
  source                 = "../../template"
  environment_name       = "test"
}
