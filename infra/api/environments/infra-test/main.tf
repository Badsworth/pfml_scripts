# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh infra-test api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "infra-test"
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
    bucket         = "massgov-pfml-infra-test-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "infra-test" {
  cluster_name = "infra-test"
}

module "api" {
  source = "../../template"

  environment_name = local.environment_name
  #st_use_mock_dor_data            = false
  #st_decrypt_dor_data             = false
  #st_file_limit_specified         = true
  service_app_count               = 2
  service_max_app_count           = 2
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.infra-test.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.5"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3506
  cors_origins = [
    "https://zj5brufqrj.execute-api.us-east-1.amazonaws.com/infra-test",
    "https://paidleave-infra-test.dfml.eol.mass.gov",
    "https://paidleave-api-infra-test.dfml.eol.mass.gov",
    # Allow requests from the Admin Portal
    "https://paidleave-admin-infra-test.dfml.eol.mass.gov",
  ]
  enable_application_fraud_check = "0"
  enable_application_import      = "1"
  enable_employee_endpoints      = "1"
  release_version                = var.release_version

  cognito_user_pool_arn       = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_8OEJk2XeD"
  cognito_user_pool_id        = "us-east-1_8OEJk2XeD"
  cognito_user_pool_client_id = "5pf01ur8rsdoumtu3ta8jvqbsj"
  cognito_user_pool_keys_url  = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_8OEJk2XeD/.well-known/jwks.json"

  # TODO: Connect to an RMV endpoint if desired. All nonprod environments are connected to the staging API
  #       in either a fully-mocked or partially-mocked setting.
  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-test/rmv_client_certificate-zWimpc"
  #using test resource for now
  rmv_api_behavior       = "fully_mocked"
  rmv_check_mock_success = "1"

  # TODO: These values are provided by FINEOS.
  fineos_client_integration_services_api_url          = ""
  fineos_client_customer_api_url                      = ""
  fineos_client_group_client_api_url                  = ""
  fineos_client_wscomposer_api_url                    = ""
  fineos_client_wscomposer_user_id                    = ""
  fineos_client_oauth2_url                            = ""
  fineos_import_employee_updates_input_directory_path = null
  fineos_aws_iam_role_arn                             = null
  fineos_aws_iam_role_external_id                     = null

  # TODO: This value is provided by FINEOS over Interchange.
  fineos_client_oauth2_client_id = ""

  pfml_email_address                  = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"

  # TODO: Connect to ServiceNow. Usually in nonprod you'll connect to test.
  service_now_base_url      = "https://savilinxtest.servicenowservices.com"
  admin_portal_base_url     = "https://paidleave-admin-infra-test.dfml.eol.mass.gov"
  azure_ad_authority_domain = "login.microsoftonline.com"
  azure_ad_client_id        = "ecc75e15-cd60-4e28-b62f-d1bf80e05d4d"
  azure_ad_parent_group     = "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD"
  azure_ad_tenant_id        = "3e861d16-48b7-4a0e-9806-8c04d81b7b2a"

  #dor_fineos_etl_schedule_expression = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour
}
