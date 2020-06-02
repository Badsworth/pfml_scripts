# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh stage api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-stage-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "stage" {
  cluster_name = "stage"
}

module "api" {
  source = "../../template"

  environment_name        = "stage"
  service_app_count       = 2
  service_docker_tag      = local.service_docker_tag
  service_ecs_cluster_arn = data.aws_ecs_cluster.stage.arn
  vpc_id                  = data.aws_vpc.vpc.id
  vpc_app_subnet_ids      = data.aws_subnet_ids.vpc_app.ids
  postgres_version        = "11.6"
  nlb_name                = "${local.vpc}-nlb"
  nlb_port                = 3500
  cors_origins = [
    # Allow requests from the Portal and API Gateway (Swagger) staging environment.
    "https://paidleave-stage.mass.gov",
    "https://day1v30d2xgnf.cloudfront.net",
    "https://paidleave-api-stage.mass.gov",
    "https://hxrjel1aeb.execute-api.us-east-1.amazonaws.com",

    # Since we're going to be pointing the Portal test environment to API staging
    # as well, allow requests to come from that origin.
    "https://paidleave-test.mass.gov",
    "https://d1ah9hpoapx4f1.cloudfront.net",

    # We're also going to allow requests from developer's machines for now, so they
    # can test certain features without deploying to the test environment. This is not
    # really that secure since anyone can spin up a local server on port 3000 and hit our
    # API, but we're not heavily using the stage environment right now so it's fine.
    "http://localhost:3000"
  ]
  dor_import_lambda_build_s3_key        = local.dor_lambda_artifact_s3_key
  dor_import_lambda_dependencies_s3_key = local.dor_import_lambda_dependencies_s3_key
}
