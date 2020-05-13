# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh prod api
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
    bucket         = "massgov-pfml-prod-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "prod" {
  cluster_name = "prod"
}

module "api" {
  source = "../../template"

  environment_name         = "prod"
  service_app_count        = 2
  service_docker_tag       = local.service_docker_tag
  service_ecs_cluster_arn  = data.aws_ecs_cluster.prod.arn
  vpc_id                   = data.aws_vpc.vpc.id
  vpc_app_subnet_ids       = data.aws_subnet_ids.vpc_app.ids
  postgres_version         = "11.6"
  db_allocated_storage     = 100
  db_max_allocated_storage = 400
  db_instance_class        = "db.r5.large"
  db_iops                  = 1000
  db_storage_type          = "io1"
  db_multi_az              = true
  nlb_name                 = "${local.vpc}-nlb"
  nlb_port                 = 80
  cors_origins = [
    # Allow requests from the Portal and API Gateway (Swagger) production environment.
    "https://pfml.eolwd.mass.gov",
    "https://d2pc6g7x2eh1yn.cloudfront.net",
    "https://pfml-api.eolwd.mass.gov",
    "https://zi7eve1v85.execute-api.us-east-1.amazonaws.com"
  ]

  dor_import_lambda_build_s3_key        = var.dor_lambda_artifact_s3_key
  dor_import_lambda_dependencies_s3_key = var.dor_import_lambda_dependencies_s3_key
}
