# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh performance api
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

locals {
  environment_name = "performance"
}

provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-performance-env-mgmt"
    key            = "terraform/api.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

data "aws_ecs_cluster" "performance" {
  cluster_name = "performance"
}

module "api" {
  source = "../../template"

  environment_name                = local.environment_name
  service_app_count               = 5 # high enough to not break immediately (?), but low enough to maybe see how autoscaling behaves in LST.
  service_max_app_count           = 10
  service_docker_tag              = local.service_docker_tag
  service_ecs_cluster_arn         = data.aws_ecs_cluster.performance.arn
  vpc_id                          = data.aws_vpc.vpc.id
  vpc_app_subnet_ids              = data.aws_subnet_ids.vpc_app.ids
  vpc_db_subnet_ids               = data.aws_subnet_ids.vpc_db.ids
  postgres_version                = "12.4"
  postgres_parameter_group_family = "postgres12"
  nlb_name                        = "${local.vpc}-nlb"
  nlb_port                        = 3501
  db_allocated_storage            = 100
  db_max_allocated_storage        = 400
  db_instance_class               = "db.r5.large" # For now, this must be changed in AWS Console. Modifications to this field will yield no result.
  db_iops                         = 1000
  db_storage_type                 = "io1" # For now, this must be changed in AWS Console. Modifications to this field will yield no result.

  cors_origins = [
    # Allow requests from the API Gateway (Swagger) and Portal performance environments.
    "https://lk64ifbnn4.execute-api.us-east-1.amazonaws.com",
    "https://dijouhh49zeeb.cloudfront.net",
    "https://paidleave-api-performance.mass.gov",
    "https://paidleave-performance.mass.gov"
  ]

  cognito_user_pool_arn       = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_0jv6SlemT"
  cognito_user_pool_id        = "us-east-1_0jv6SlemT"
  cognito_user_pool_client_id = "1ps8bs9s5ns4f6qamj6qn6qd3"
  cognito_user_pool_keys_url  = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_0jv6SlemT/.well-known/jwks.json"

  cognito_enable_provisioned_concurrency              = true
  logging_level                                       = "massgov.pfml.fineos.fineos_client=DEBUG"
  rmv_client_base_url                                 = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn                   = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-performance/rmv_client_certificate-fXNkdl"
  rmv_check_behavior                                  = "partially_mocked"
  rmv_check_mock_success                              = "1"
  fineos_client_integration_services_api_url          = "https://perf-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url                  = "https://perf-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_customer_api_url                      = "https://perf-api.masspfml.fineos.com/customerapi/"
  fineos_client_wscomposer_api_url                    = "https://perf-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://perf-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                      = "5u0hcdodd6vt5bfa6p2u6ij13d"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/PERF/dataexports"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"
  service_now_base_url                                = "https://savilinxstage.servicenowservices.com"
  portal_base_url                                     = "https://paidleave-performance.mass.gov"
  enable_application_fraud_check                      = "0"
  release_version                                     = var.release_version
}
