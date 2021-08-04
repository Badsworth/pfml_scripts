# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh cps-preview api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "cps-preview"
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
    bucket         = "massgov-pfml-cps-preview-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "cps-preview" {
  cluster_name = "cps-preview"
}

module "api" {
  source = "../../template"

  environment_name                = local.environment_name
  service_app_count               = 2
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.cps-preview.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.4"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3505
  cors_origins = [
    "https://paidleave-cps-preview.eol.mass.gov",
    "https://paidleave-api-cps-preview.eol.mass.gov",
  ]
  enable_application_fraud_check = "0"
  release_version                = var.release_version

  cognito_user_pool_arn       = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_1OVYp4aZo"
  cognito_user_pool_id        = "us-east-1_1OVYp4aZo"
  cognito_user_pool_client_id = "59oeobfn0759c8166pjh381joc"
  cognito_user_pool_keys_url  = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_1OVYp4aZo/.well-known/jwks.json"
  portal_base_url             = "https://paidleave-cps-preview.eol.mass.gov"

  logging_level = "massgov.pfml.fineos.fineos_client=DEBUG"

  # TODO: Connect to an RMV endpoint if desired. All nonprod environments are connected to the staging API
  #       in either a fully-mocked or partially-mocked setting.
  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-cps-preview/rmv_client_certificate-alAlg3"
  rmv_check_behavior                = "partially_mocked"
  rmv_check_mock_success            = "1"

  # TODO: These values are provided by FINEOS.
  fineos_client_integration_services_api_url          = "https://dt3-api.masspfml.fineos.com/integration-services/"
  fineos_client_customer_api_url                      = "https://dt3-api.masspfml.fineos.com/customerapi/"
  fineos_client_group_client_api_url                  = "https://dt3-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url                    = "https://dt3-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://dt3-api.masspfml.fineos.com/oauth2/token"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/DT3/dataexports"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"

  # TODO: This value is provided by FINEOS over Interchange.
  fineos_client_oauth2_client_id = "2gptm2870hlo9ouq70poib8d5g"

  # TODO: Connect to ServiceNow.
  service_now_base_url = "https://savilinxstage.servicenowservices.com"
}
