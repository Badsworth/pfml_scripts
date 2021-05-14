# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh stage api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "stage"
}

provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-stage-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "stage" {
  cluster_name = "stage"
}

module "api" {
  source = "../../template"

  environment_name                = local.environment_name
  service_app_count               = 2 # because stage is a low-demand environment
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.stage.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.4"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3500
  cors_origins = [
    # Allow requests from the Portal and API Gateway (Swagger) staging environment.
    "https://paidleave-stage.mass.gov",
    "https://day1v30d2xgnf.cloudfront.net",
    "https://paidleave-api-stage.mass.gov",
    "https://hxrjel1aeb.execute-api.us-east-1.amazonaws.com",

    # Since we're going to be pointing the Portal test environment to API staging
    # as well, allow requests to come from that origin.
    "https://paidleave-test.mass.gov",
    "https://d1ah9hpoapx4f1.cloudfront.net",

    # We're also going to allow requests from Portal developer's machines for now, so they
    # can test certain features without deploying to the test environment. This is not
    # really that secure since anyone can spin up a local server on port 3000 and hit our
    # API, but we're not heavily using the stage environment right now so it's fine.
    "http://localhost:3000"
  ]

  cognito_user_pool_arn                               = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_HpL4XslLg"
  cognito_user_pool_id                                = "us-east-1_HpL4XslLg"
  cognito_user_pool_client_id                         = "10rjcp71r8bnk4459c67bn18t8"
  cognito_user_pool_keys_url                          = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_HpL4XslLg/.well-known/jwks.json"
  cognito_post_confirmation_lambda_artifact_s3_key    = local.cognito_post_confirmation_lambda_artifact_s3_key
  cognito_pre_signup_lambda_artifact_s3_key           = local.cognito_pre_signup_lambda_artifact_s3_key
  cognito_enable_provisioned_concurrency              = false
  logging_level                                       = "massgov.pfml.fineos.fineos_client=DEBUG"
  rmv_client_base_url                                 = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn                   = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-stage/rmv_client_certificate-QlZaMl"
  rmv_check_behavior                                  = "partially_mocked"
  rmv_check_mock_success                              = "1"
  enforce_leave_admin_verification                    = "1"
  fineos_client_customer_api_url                      = "https://idt-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url          = "https://idt-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url                  = "https://idt-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url                    = "https://idt-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://idt-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                      = "1fa281uto9tjuqtm21jle7loam"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/IDT/dataexports"
  service_now_base_url                                = "https://savilinxstage.servicenowservices.com"
  portal_base_url                                     = "https://paidleave-stage.mass.gov"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"
  enable_application_fraud_check                      = "0"
  dor_fineos_etl_schedule_expression                  = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour
  release_version                                     = var.release_version
}
