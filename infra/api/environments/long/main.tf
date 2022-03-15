# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh long api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "long"
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
    bucket         = "massgov-pfml-long-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "long" {
  cluster_name = "long"
}

module "api" {
  source = "../../template"

  logging_level = "massgov.pfml.fineos.fineos_client=DEBUG"

  environment_name = local.environment_name
  # st_use_mock_dor_data    = false
  # st_decrypt_dor_data     = false
  # st_file_limit_specified = true
  service_app_count               = 2
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.long.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.5"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3507
  cors_origins = [
    "https://paidleave-long.dfml.eol.mass.gov",
    "https://paidleave-api-long.dfml.eol.mass.gov",
    # Allow requests from the Admin Portal
    "https://paidleave-admin-long.dfml.eol.mass.gov",
  ]
  enable_application_fraud_check = "0"
  release_version                = var.release_version

  cognito_user_pool_arn       = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_FADLpF6um"
  cognito_user_pool_id        = "us-east-1_FADLpF6um"
  cognito_user_pool_client_id = "1ufb6r40s1ad0evjffvdtl3113"
  cognito_user_pool_keys_url  = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_FADLpF6um/.well-known/jwks.json"


  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-long/rmv_client_certificate-V8Pnt1"
  rmv_api_behavior                  = "fully_mocked"
  rmv_check_mock_success            = "1"

  fineos_client_integration_services_api_url          = "https://dt4-api.masspfml.fineos.com/integration-services/"
  fineos_client_customer_api_url                      = "https://dt4-api.masspfml.fineos.com/customerapi/"
  fineos_client_group_client_api_url                  = "https://dt4-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url                    = "https://dt4-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://dt4-api.masspfml.fineos.com/oauth2/token"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/DT4/dataexports"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"

  fineos_client_oauth2_client_id = "5744bq9dpveko6jie4ma1e4g93"

  fineos_is_running_v21 = "true"

  admin_portal_base_url               = "https://paidleave-admin-long.dfml.eol.mass.gov"
  pfml_email_address                  = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"

  service_now_base_url = "https://savilinxlong.servicenowservices.com"
  portal_base_url      = "https://paidleave-long.dfml.eol.mass.gov"

  # dor_fineos_etl_schedule_expression               = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour

  azure_ad_authority_domain = "login.microsoftonline.com"
  azure_ad_client_id        = "ecc75e15-cd60-4e28-b62f-d1bf80e05d4d"
  azure_ad_parent_group     = "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD"
  azure_ad_tenant_id        = "3e861d16-48b7-4a0e-9806-8c04d81b7b2a"

  enable_document_multipart_upload = "1"
  enable_application_import        = "1"
  enable_employee_endpoints        = "1"
}
