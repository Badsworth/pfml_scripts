# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh test api
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

  environment_name        = "test"
  service_app_count       = 2
  service_docker_tag      = local.service_docker_tag
  service_ecs_cluster_arn = data.aws_ecs_cluster.test.arn
  vpc_id                  = data.aws_vpc.vpc.id
  vpc_app_subnet_ids      = data.aws_subnet_ids.vpc_app.ids
  postgres_version        = "11.6"
  nlb_name                = "${local.vpc}-nlb"
  nlb_port                = 80
  enable_full_error_logs  = "1"
  cors_origins = [
    # Allow requests from the Portal and API Gateway (Swagger) test environment.
    "https://paidleave-test.mass.gov",
    "https://d1ah9hpoapx4f1.cloudfront.net",
    "https://paidleave-api-test.mass.gov",
    "https://67385ye4yb.execute-api.us-east-1.amazonaws.com"
  ]
  dor_import_lambda_build_s3_key        = local.dor_lambda_artifact_s3_key
  dor_import_lambda_dependencies_s3_key = local.dor_import_lambda_dependencies_s3_key
  formstack_import_lambda_build_s3_key  = local.formstack_lambda_artifact_s3_key

  cognito_user_pool_arn                            = "arn:aws:cognito-idp:us-east-1:498823821309:userpool/us-east-1_HhQSLYSIe"
  cognito_post_confirmation_lambda_artifact_s3_key = local.cognito_post_confirmation_lambda_artifact_s3_key
  cognito_user_pool_keys_url                       = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_HhQSLYSIe/.well-known/jwks.json"
  rmv_client_base_url                              = "https://atlas-staging-gateway.massdot.state.ma.us"
  rmv_client_certificate_binary_arn                = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-test/rmv_client_certificate-zWimpc"
  fineos_client_customer_api_url                   = "https://dt2-api.masspfml.fineos.com/customer-services/"
  fineos_client_wscomposer_api_url                 = "https://dt2-claims-webapp.masspfml.fineos.com/wscomposer/"
  fineos_client_oauth2_url                         = "https://dt2-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                   = "1ral5e957i0l9shul52bhk0037"
  fineos_eligibility_transfer_lambda_build_s3_key  = local.fineos_eligibility_transfer_lambda_build_s3_key
}
