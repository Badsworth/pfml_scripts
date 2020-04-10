# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh $ENV_NAME env
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-$ENV_NAME-env-mgmt"
    key            = "terraform/env.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  domain_name      = "pfml"
  environment_name = "$ENV_NAME"
}
