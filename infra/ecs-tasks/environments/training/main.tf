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
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name         = "training"
  st_use_mock_dor_data     = false
  st_decrypt_dor_data      = false
  st_file_limit_specified  = false
  st_employer_update_limit = 1500
  service_docker_tag       = local.service_docker_tag
  vpc_id                   = data.aws_vpc.vpc.id
  app_subnet_ids           = data.aws_subnet_ids.vpc_app.ids

  cognito_user_pool_id                       = "us-east-1_gHLjkp4A8"
  fineos_client_integration_services_api_url = "https://trn-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url         = "https://trn-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_customer_api_url             = "https://trn-api.masspfml.fineos.com/customerapi/"
  fineos_client_wscomposer_api_url           = "https://trn-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                   = "https://trn-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "2jdpsthb76p5rfhfl9bdjem8gf"

  fineos_aws_iam_role_arn         = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id = "12345"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-somdev-data-import/TRN"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/TRN/dataexports"
  fineos_error_export_path                            = "s3://fin-somdev-data-export/TRN/errorExtracts"
  fineos_report_export_path                           = "s3://fin-somdev-data-export/TRN/reportExtracts"

  enable_register_admins_job = true

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]

  dor_fineos_etl_schedule_expression = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour
}
