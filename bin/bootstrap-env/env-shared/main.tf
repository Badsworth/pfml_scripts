# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh $ENV_NAME env-shared
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

locals {
  vpc = "$ENV_NAME" == "prod" ? "prod" : "nonprod"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-$ENV_NAME-env-mgmt"
    key            = "terraform/env-shared.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "pfml" {
  source = "../../template"

  environment_name  = "$ENV_NAME"
  # TODO: This will revert back to '/api/' once we have a custom domain name.
  #       For now, we're relying on the API Gateway-provided URL which prepends
  #       the "$ENV_NAME" stage.
  forwarded_path    = "'/$ENV_NAME/api/'"
  nlb_name          = "${local.vpc}-nlb"
  nlb_vpc_link_name = "${local.vpc}-nlb-vpc-link"
  nlb_port          = CHOOSE_UNIQUE_PROXY_PORT_FOR_ENVIRONMENT
}
