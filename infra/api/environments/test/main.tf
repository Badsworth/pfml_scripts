# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh test api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "test"
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
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "test" {
  cluster_name = "test"
}

module "api" {
  source = "../../template"

  environment_name                = local.environment_name
  service_app_count               = 3 # because test is used often for development and UAT
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.test.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.4"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 80
  enable_full_error_logs          = "1"

  # Disable test Cloudwatch alarms temporarily until API-1062 is resolved.
  # https://lwd.atlassian.net/browse/API-1062
  enable_alarm_api_cpu = false
  enable_alarm_api_ram = false

  cors_origins = [
    # Allow requests from the Portal and API Gateway (Swagger) test environment.
    "https://paidleave-test.mass.gov",
    "https://d1ah9hpoapx4f1.cloudfront.net",
    "https://paidleave-api-test.mass.gov",
    "https://67385ye4yb.execute-api.us-east-1.amazonaws.com",

    # Allow requests from the Admin Portal
    "https://paidleave-admin-test.dfml.eol.mass.gov",

    # Since we may temporarily point the Portal stage environment to API test
    # as well, allow requests to come from that origin.
    # Example: https://lwd.atlassian.net/browse/CP-1063
    "https://paidleave-stage.mass.gov",

    # We're also going to allow requests from Portal developer's machines for now, so they
    # can test certain features without deploying to the test environment. This is not
    # really that secure since anyone can spin up a local server on port 3000 and hit our
    # API, but we're not heavily using the test environment right now so it's fine.
    "http://localhost:3000",
    # Local server on port 3001 for the Admin Portal
    "http://localhost:3001"
  ]

  cognito_user_pool_arn                               = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_HhQSLYSIe"
  cognito_user_pool_id                                = "us-east-1_HhQSLYSIe"
  cognito_user_pool_client_id                         = "7sjb96tvg8251lrq5vdk7de9"
  cognito_user_pool_keys_url                          = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_HhQSLYSIe/.well-known/jwks.json"
  cognito_enable_provisioned_concurrency              = false
  logging_level                                       = "massgov.pfml.fineos.fineos_client=DEBUG"
  rmv_client_base_url                                 = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn                   = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-test/rmv_client_certificate-zWimpc"
  rmv_api_behavior                                    = "fully_mocked"
  rmv_check_mock_success                              = "1"
  fineos_client_integration_services_api_url          = "https://dt2-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url                  = "https://dt2-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_customer_api_url                      = "https://dt2-api.masspfml.fineos.com/customerapi/"
  fineos_client_wscomposer_api_url                    = "https://dt2-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://dt2-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                      = "1ral5e957i0l9shul52bhk0037"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/DT2/dataexports"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"
  pfml_email_address                                  = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn                 = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  service_now_base_url                                = "https://savilinxtest.servicenowservices.com"
  portal_base_url                                     = "https://paidleave-test.mass.gov"
  admin_portal_base_url                               = "https://paidleave-admin-test.dfml.eol.mass.gov"
  azure_ad_authority_domain                           = "login.microsoftonline.com"
  azure_ad_client_id                                  = "ecc75e15-cd60-4e28-b62f-d1bf80e05d4d"
  azure_ad_parent_group                               = "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD"
  azure_ad_tenant_id                                  = "3e861d16-48b7-4a0e-9806-8c04d81b7b2a"
  enable_application_fraud_check                      = "0"
  release_version                                     = var.release_version

  enable_document_multipart_upload = "1"
  enable_application_import        = "1"
  enable_employee_endpoints        = "1"
}
