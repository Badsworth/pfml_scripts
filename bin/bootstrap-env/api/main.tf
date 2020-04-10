# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh $ENV_NAME api
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
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "$ENV_NAME" {
  cluster_name = "$ENV_NAME"
}

module "api" {
  source = "../../template"

  environment_name        = "$ENV_NAME"
  service_app_count       = 2
  service_docker_tag      = local.service_docker_tag
  service_ecs_cluster_arn = data.aws_ecs_cluster.$ENV_NAME.arn
  vpc_id                  = data.aws_vpc.vpc.id
  vpc_app_subnet_ids      = data.aws_subnet_ids.vpc_app.ids
  postgres_version        = "11.6"
}
