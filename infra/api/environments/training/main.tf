# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh training api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "training"
}

provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-training-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "training" {
  cluster_name = "training"
}

module "api" {
  source = "../../template"

  environment_name                = local.environment_name
  service_app_count               = 2 # because training is a very low-demand environment
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.training.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.4"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3502
  cors_origins = [
    # Allow requests from the API Gateway (Swagger) and Portal training environments.
    "https://mo0nk02mkg.execute-api.us-east-1.amazonaws.com",
    "https://dist3ws941qq9.cloudfront.net",
    "https://paidleave-api-training.mass.gov",
    "https://paidleave-training.mass.gov",
    # Allow requests from the Admin Portal
    "https://paidleave-admin-training.dfml.eol.mass.gov",
  ]

  cognito_user_pool_arn                               = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_gHLjkp4A8"
  cognito_user_pool_id                                = "us-east-1_gHLjkp4A8"
  cognito_user_pool_client_id                         = "2hr6bckdopamvq92jahr542p5p"
  cognito_user_pool_keys_url                          = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_gHLjkp4A8/.well-known/jwks.json"
  cognito_enable_provisioned_concurrency              = false
  rmv_client_base_url                                 = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn                   = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-training/rmv_client_certificate-uUtNEp"
  rmv_api_behavior                                    = "partially_mocked"
  rmv_check_mock_success                              = "1"
  fineos_client_integration_services_api_url          = "https://trn-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url                  = "https://trn-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_customer_api_url                      = "https://trn-api.masspfml.fineos.com/customerapi/"
  fineos_client_wscomposer_api_url                    = "https://trn-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://trn-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                      = "2jdpsthb76p5rfhfl9bdjem8gf"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/TRN/dataexports"
  fineos_aws_iam_role_arn                             = null // TODO if needed
  fineos_aws_iam_role_external_id                     = null // TODO if needed
  pfml_email_address                                  = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn                 = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  service_now_base_url                                = "https://savilinxtrain.servicenowservices.com"
  admin_portal_base_url                               = "https://paidleave-admin-training.dfml.eol.mass.gov"
  portal_base_url                                     = "https://paidleave-training.mass.gov"
  enable_application_fraud_check                      = "0"
  release_version                                     = var.release_version

  azure_ad_authority_domain = "login.microsoftonline.com"
  azure_ad_client_id        = "ecc75e15-cd60-4e28-b62f-d1bf80e05d4d"
  azure_ad_parent_group     = "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD"
  azure_ad_tenant_id        = "3e861d16-48b7-4a0e-9806-8c04d81b7b2a"

  enable_employee_endpoints = "1"
}
