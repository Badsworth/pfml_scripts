provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-prod-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
  }
}

module "tasks" {
  source = "../../template"

  environment_name   = "prod"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id

  cognito_user_pool_id                       = "us-east-1_UwxnhD1cG"
  fineos_client_customer_api_url             = "https://prd-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url = "https://prd-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url         = "https://prd-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url           = "https://prd-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_wscomposer_user_id           = "OASIS"
  fineos_client_oauth2_url                   = "https://prd-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "5qcd2h1qlv4gpiqgugn2mrttkg"

  fineos_aws_iam_role_arn         = "arn:aws:iam::133945341851:role/somprod-IAMRoles-CustomerAccountAccessRole-83KBPT56FTQP"
  fineos_aws_iam_role_external_id = "8jFBtjr4UA@"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-somprod-data-import/PRD"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somprod-data-export/PRD/dataexports"
}
