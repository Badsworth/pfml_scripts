# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh trn2 api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "trn2"
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
    bucket         = "massgov-pfml-trn2-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "trn2" {
  cluster_name = "trn2"
}

module "api" {
  source = "../../template"

  environment_name = local.environment_name
  # st_use_mock_dor_data    = false
  # st_decrypt_dor_data     = false
  # st_file_limit_specified = true
  service_app_count               = 2
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.trn2.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.5"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3508
  cors_origins = [
    "https://paidleave-trn2.eol.mass.gov",
    "https://paidleave-api-trn2.eol.mass.gov",
  ]
  enable_application_fraud_check = "0"
  release_version                = var.release_version

  cognito_user_pool_arn       = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_oxOGrdAe8"
  cognito_user_pool_id        = "us-east-1_oxOGrdAe8"
  cognito_user_pool_client_id = "3dgp7vtcdt7bo0utlp2tqit1ee"
  cognito_user_pool_keys_url  = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_oxOGrdAe8/.well-known/jwks.json"

  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-trn2/rmv_client_certificate-D5TPeE"
  rmv_api_behavior                  = "fully_mocked"
  rmv_check_mock_success            = "1"

  fineos_client_integration_services_api_url          = "https://trn2-api.masspfml.fineos.com/integration-services"
  fineos_client_customer_api_url                      = "https://trn2-api.masspfml.fineos.com/customerapi/customer"
  fineos_client_group_client_api_url                  = "https://trn2-api.masspfml.fineos.com/groupclientapi/groupClient"
  fineos_client_wscomposer_api_url                    = "https://trn2-api.masspfml.fineos.com/integration-services/wscomposer/webservice"
  fineos_client_oauth2_url                            = "https://trn2-api.masspfml.fineos.com/oauth2/token"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-import/TRN2/absence-eligibility/upload/"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"

  fineos_client_oauth2_client_id = "2e9vsuq808h3tu4rf9tr1efuh5"

  service_now_base_url = "https://savilinxtrain.servicenowservices.com"

  # dor_fineos_etl_schedule_expression               = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour

  enable_pdf_document_compression = "0"
}
