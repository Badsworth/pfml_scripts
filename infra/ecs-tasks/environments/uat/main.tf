locals {
  environment_name = "uat"
}
provider "aws" {
  region  = "us-east-1"
  version = "3.74.1"
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

  environment_name              = "uat"
  st_use_mock_dor_data          = false
  st_decrypt_dor_data           = false
  st_file_limit_specified       = true
  st_employer_update_limit      = 1500
  service_docker_tag            = local.service_docker_tag
  vpc_id                        = data.aws_vpc.vpc.id
  app_subnet_ids                = data.aws_subnet_ids.vpc_app.ids
  enforce_execute_sql_read_only = false


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

  fineos_eligibility_feed_output_directory_path       = "s3://fin-sompre-data-import/UAT"
  fineos_import_employee_updates_input_directory_path = "s3://fin-sompre-data-export/UAT/dataexports"

  fineos_data_export_path       = "s3://fin-sompre-data-export/UAT/dataexports"
  fineos_adhoc_data_export_path = "s3://fin-somdev-data-export/UAT/dataExtracts/AdHocExtract"
  fineos_data_import_path       = "s3://fin-sompre-data-import/UAT/peiupdate"
  fineos_error_export_path      = "s3://fin-sompre-data-export/UAT/errorExtracts"
  fineos_report_export_path     = "s3://fin-sompre-data-export/UAT/reportExtract"

  enable_pub_automation_fineos                     = true
  enable_pub_automation_create_pub_files           = true
  enable_pub_automation_process_returns            = false
  enable_fineos_import_iaww                        = true
  enable_standalone_fineos_import_employee_updates = true

  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-uat/rmv_client_certificate-LWvMFe"
  rmv_api_behavior                  = "partially_mocked"

  logging_level = "massgov.pfml.fineos.fineos_client=DEBUG"

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]

  # Daily at [20:30 Eastern]
  dor_fineos_etl_schedule_expression_standard                                    = "cron(30 1 * * ? *)"
  dor_fineos_etl_schedule_expression_daylight_savings                            = "cron(30 0 * * ? *)"
  standalone_fineos_import_employee_updates_schedule_expression_standard         = "cron(30 13 * * ? *)"
  standalone_fineos_import_employee_updates_schedule_expression_daylight_savings = "cron(30 12 * * ? *)"

  pdf_api_host                    = "http://localhost:5000"
  enable_generate_1099_pdf        = "0"
  generate_1099_max_files         = "1000"
  enable_merge_1099_pdf           = "0"
  enable_upload_1099_pdf          = "0"
  upload_max_files_to_fineos      = "10"
  enable_1099_testfile_generation = "0"
  irs_1099_correction_ind         = "0"

  enable_employer_reimbursement_payments = "0"

  enable_pub_payments_copy_audit_report_schedule = true
}
