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
  required_version = "0.12.24"

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

  environment_name                      = "$ENV_NAME"
  service_app_count                     = 2
  service_docker_tag                    = local.service_docker_tag
  service_ecs_cluster_arn               = data.aws_ecs_cluster.$ENV_NAME.arn
  vpc_id                                = data.aws_vpc.vpc.id
  vpc_app_subnet_ids                    = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids                     = data.aws_subnet_ids.vpc_db.ids
  postgres_version                      = "12.4"
  postgres_parameter_group_family       = "postgres12"
  nlb_name                              = "\${local.vpc}-nlb"
  nlb_port                              = UNIQUE_NLB_PORT_RESERVED_IN_ENV_SHARED
  cors_origins                          = [API_DOCS_DOMAIN, PORTAL_DOMAIN]
  formstack_import_lambda_build_s3_key  = local.formstack_lambda_artifact_s3_key

  cognito_user_pool_arn                            = null
  cognito_user_pool_keys_url                       = ""
  cognito_post_confirmation_lambda_artifact_s3_key = local.cognito_post_confirmation_lambda_artifact_s3_key
  cognito_pre_signup_lambda_artifact_s3_key        = local.cognito_pre_signup_lambda_artifact_s3_key
  fineos_eligibility_transfer_lambda_build_s3_key  = local.fineos_eligibility_transfer_lambda_build_s3_key
  rmv_client_base_url                              = null
  rmv_client_certificate_binary_arn                = null
  rmv_check_behavior                               = "fully_mocked"
  rmv_check_mock_success                           = "1"
  fineos_client_integration_services_api_url       = ""
  fineos_client_customer_api_url                   = ""
  fineos_client_group_client_api_url               = ""
  fineos_client_wscomposer_api_url                 = ""
  fineos_client_oauth2_url                         = ""
  fineos_client_oauth2_client_id                   = ""
  fineos_eligibility_feed_output_directory_path    = null
  fineos_aws_iam_role_arn                          = null
  fineos_aws_iam_role_external_id                  = null
  enable_employer_endpoints                        = "1"
  enable_application_fraud_check                   = "0"
}
