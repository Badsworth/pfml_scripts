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
    bucket         = "massgov-pfml-uat-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name   = "uat"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id
  app_subnet_ids     = data.aws_subnet_ids.vpc_app.ids

  cognito_user_pool_id                       = "us-east-1_29j6fKBDT"
  fineos_client_customer_api_url             = "https://uat-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url = "https://uat-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url         = "https://uat-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url           = "https://uat-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_wscomposer_user_id           = "OASIS"
  fineos_client_oauth2_url                   = "https://uat-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "61on8s7n66i0gj913didkmn5q"

  fineos_aws_iam_role_arn         = "arn:aws:iam::016390658835:role/sompre-IAMRoles-CustomerAccountAccessRole-S0EP9ABIA02Z"
  fineos_aws_iam_role_external_id = "8jFBtjr4UA@"
  enable_sentry                   = "0"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-sompre-data-import/UAT"
  fineos_import_employee_updates_input_directory_path = "s3://fin-sompre-data-export/UAT/dataexports"
  fineos_error_export_path                            = "s3://fin-sompre-data-export/UAT/errorExtracts"
  logging_level                                       = "massgov.pfml.fineos.fineos_client=DEBUG"

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]
}
