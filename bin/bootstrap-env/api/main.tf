# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh $ENV_NAME api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "$ENV_NAME"
}

provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    newrelic = {
      source = "newrelic/newrelic"
    }
    pagerduty = {
      source = "pagerduty/pagerduty"
    }
  }
    
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

  environment_name                      = local.environment_name
  service_app_count                     = 2
  service_max_app_count                 = 10
  service_docker_tag                    = local.service_docker_tag
  service_ecs_cluster_arn               = data.aws_ecs_cluster.$ENV_NAME.arn
  vpc_id                                = data.aws_vpc.vpc.id
  vpc_app_subnet_ids                    = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids                     = data.aws_subnet_ids.vpc_db.ids
  postgres_version                      = "12.5"
  postgres_parameter_group_family       = "postgres12"
  nlb_name                              = "\${local.vpc}-nlb"
  nlb_port                              = UNIQUE_NLB_PORT_RESERVED_IN_ENV_SHARED
  cors_origins                          = [API_DOCS_DOMAIN, PORTAL_DOMAIN]
  enforce_leave_admin_verification                 = "0"
  enable_application_fraud_check                   = "0"
  release_version = var.release_version

  # TODO: Fill this in after the portal is deployed.
  cognito_user_pool_arn                            = null
  cognito_user_pool_id                             = ""
  cognito_user_pool_client_id                      = ""
  cognito_user_pool_keys_url                       = ""

  cognito_post_confirmation_lambda_artifact_s3_key = local.cognito_post_confirmation_lambda_artifact_s3_key
  cognito_pre_signup_lambda_artifact_s3_key        = local.cognito_pre_signup_lambda_artifact_s3_key

  # TODO: Connect to an RMV endpoint if desired. All nonprod environments are connected to the staging API
  #       in either a fully-mocked or partially-mocked setting.
  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = ARN_FROM_SECRETS_MANAGER_OUTPUT
  rmv_check_behavior                = "fully_mocked"
  rmv_check_mock_success            = "1"

  # TODO: These values are provided by FINEOS.
  fineos_client_integration_services_api_url       = ""
  fineos_client_customer_api_url                   = ""
  fineos_client_group_client_api_url               = ""
  fineos_client_wscomposer_api_url                 = ""
  fineos_client_wscomposer_user_id                 = ""
  fineos_client_oauth2_url                         = ""
  fineos_import_employee_updates_input_directory_path = null
  fineos_aws_iam_role_arn                          = null
  fineos_aws_iam_role_external_id                  = null

  # TODO: This value is provided by FINEOS over Interchange.
  fineos_client_oauth2_client_id                   = ""

  # TODO: Connect to ServiceNow. Usually in nonprod you'll connect to stage.
  service_now_base_url = "https://savilinxstage.servicenowservices.com"

  dor_fineos_etl_definition                        = local.dor_fineos_etl_definition
  dor_fineos_etl_schedule_expression               = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour
}
