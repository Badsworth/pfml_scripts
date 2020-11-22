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
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
  }
}

data "aws_ecs_cluster" "prod" {
  cluster_name = "prod"
}

module "api" {
  source = "../../template"

  environment_name                = "prod"
  service_app_count               = 2
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
  db_instance_class               = "db.r5.large"
  db_iops                         = 1000
  db_storage_type                 = "io1"
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
  cognito_user_pool_keys_url                       = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_UwxnhD1cG/.well-known/jwks.json"
  cognito_post_confirmation_lambda_artifact_s3_key = local.cognito_post_confirmation_lambda_artifact_s3_key
  cognito_pre_signup_lambda_artifact_s3_key        = local.cognito_pre_signup_lambda_artifact_s3_key
  formstack_import_lambda_build_s3_key             = local.formstack_lambda_artifact_s3_key
  rmv_client_base_url                              = "https://atlas-gateway.massdot.state.ma.us"
  rmv_client_certificate_binary_arn                = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-prod/rmv_client_certificate-Mo2HJu"
  rmv_check_behavior                               = "partially_mocked"
  rmv_check_mock_success                           = "1"
  fineos_client_customer_api_url                   = "https://prd-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url       = "https://prd-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url               = "https://prd-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url                 = "https://prd-claims-webapp.masspfml.fineos.com/wscomposer/"
  fineos_client_wscomposer_user_id                 = "OASIS"
  fineos_client_oauth2_url                         = "https://prd-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                   = "5qcd2h1qlv4gpiqgugn2mrttkg"
  fineos_eligibility_transfer_lambda_build_s3_key  = local.fineos_eligibility_transfer_lambda_build_s3_key
  enable_employer_endpoints                        = "0"
  enable_application_fraud_check                   = "0"
}
