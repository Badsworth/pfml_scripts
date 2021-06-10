# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh prod api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "prod"
}

provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-prod-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
  }
}

data "aws_ecs_cluster" "prod" {
  cluster_name = "prod"
}

module "api" {
  source = "../../template"

  environment_name                = local.environment_name
  service_app_count               = 10 # no need to take risks in prod on day one.
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.prod.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.4"
  postgres_parameter_group_family = "postgres12"
  db_allocated_storage            = 100
  db_max_allocated_storage        = 400
  db_instance_class               = "db.r5.large" # For now, this must be changed in AWS Console. Modifications to this field will yield no result.
  db_iops                         = 1000
  db_storage_type                 = "io1" # For now, this must be changed in AWS Console. Modifications to this field will yield no result.
  db_multi_az                     = true
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 80
  cors_origins = [
    # Allow requests from the Portal and API Gateway (Swagger) production environment.
    "https://paidleave.mass.gov",
    "https://d2pc6g7x2eh1yn.cloudfront.net",
    "https://paidleave-api.mass.gov",
    "https://zi7eve1v85.execute-api.us-east-1.amazonaws.com"
  ]

  cognito_user_pool_arn                            = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_UwxnhD1cG"
  cognito_user_pool_id                             = "us-east-1_UwxnhD1cG"
  cognito_user_pool_client_id                      = "64p5sdtqul5a4pn3ikbscjhujn"
  cognito_user_pool_keys_url                       = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_UwxnhD1cG/.well-known/jwks.json"
  cognito_post_confirmation_lambda_artifact_s3_key = local.cognito_post_confirmation_lambda_artifact_s3_key
  cognito_pre_signup_lambda_artifact_s3_key        = local.cognito_pre_signup_lambda_artifact_s3_key
  cognito_enable_provisioned_concurrency           = true
  rmv_client_base_url                              = "https://atlas-gateway.massdot.state.ma.us"
  rmv_client_certificate_binary_arn                = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-prod/rmv_client_certificate-Mo2HJu"
  rmv_client_server_ca_bundle_name                 = "2021"
  rmv_check_behavior                               = "not_mocked"
  fineos_client_customer_api_url                   = "https://prd-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url       = "https://prd-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url               = "https://prd-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url                 = "https://prd-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_wscomposer_user_id                 = "OASIS"
  fineos_client_oauth2_url                         = "https://prd-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                   = "5qcd2h1qlv4gpiqgugn2mrttkg"
  service_now_base_url                             = "https://savilinx.servicenowservices.com"
  portal_base_url                                  = "https://paidleave.mass.gov"
  enable_application_fraud_check                   = "1"
  fineos_aws_iam_role_arn                          = "arn:aws:iam::133945341851:role/somprod-IAMRoles-CustomerAccountAccessRole-83KBPT56FTQP"
  fineos_aws_iam_role_external_id                  = "8jFBtjr4UA@"

  fineos_import_employee_updates_input_directory_path = "s3://fin-somprod-data-export/PRD/dataexports"

  release_version = var.release_version
}
