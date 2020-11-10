# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh performance api
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

  environment_name                = "performance"
  service_app_count               = 2
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
  db_instance_class               = "db.r5.large"
  db_iops                         = 1000
  db_storage_type                 = "io1"

  cors_origins = [
    # Allow requests from the API Gateway (Swagger) performance environment.
    "https://lk64ifbnn4.execute-api.us-east-1.amazonaws.com"
    // TODO: PORTAL_DOMAIN CP-1620/API-771
  ]
  formstack_import_lambda_build_s3_key = local.formstack_lambda_artifact_s3_key

  cognito_user_pool_arn                            = null                                                                                    // TODO API-771
  cognito_user_pool_keys_url                       = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_HhQSLYSIe/.well-known/jwks.json" // TODO: Update in API-771
  cognito_post_confirmation_lambda_artifact_s3_key = local.cognito_post_confirmation_lambda_artifact_s3_key
  rmv_client_base_url                              = "https://atlas-staging-gateway.massdot.state.ma.us"
  rmv_client_certificate_binary_arn                = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-performance/rmv_client_certificate-fXNkdl"
  rmv_check_behavior                               = "partially_mocked"
  rmv_check_mock_success                           = "1"
  fineos_client_integration_services_api_url       = "https://perf-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url               = "https://perf-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_customer_api_url                   = "https://perf-api.masspfml.fineos.com/customerapi/"
  fineos_client_wscomposer_api_url                 = "https://perf-claims-webapp.masspfml.fineos.com/wscomposer/"
  fineos_client_oauth2_url                         = "https://perf-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                   = "5u0hcdodd6vt5bfa6p2u6ij13d"
  fineos_eligibility_transfer_lambda_build_s3_key  = local.fineos_eligibility_transfer_lambda_build_s3_key
  fineos_eligibility_feed_output_directory_path    = "s3://fin-somdev-data-import/PERF/absence-eligibility/upload"
  fineos_aws_iam_role_arn                          = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                  = "12345"
  enable_employer_endpoints                        = "1"
}
