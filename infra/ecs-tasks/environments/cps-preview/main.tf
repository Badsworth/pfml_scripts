locals {
  environment_name = "cps-preview"
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
    bucket         = "massgov-pfml-cps-preview-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name              = "cps-preview"
  st_use_mock_dor_data          = false
  st_decrypt_dor_data           = false
  st_file_limit_specified       = true
  st_employer_update_limit      = 1500
  service_docker_tag            = local.service_docker_tag
  vpc_id                        = data.aws_vpc.vpc.id
  app_subnet_ids                = data.aws_subnet_ids.vpc_app.ids
  enforce_execute_sql_read_only = false

  cognito_user_pool_id = "us-east-1_1OVYp4aZo"

  # TODO: These values are provided by FINEOS.
  fineos_client_integration_services_api_url          = "https://dt3-api.masspfml.fineos.com/integration-services/"
  fineos_client_customer_api_url                      = "https://dt3-api.masspfml.fineos.com/customerapi/"
  fineos_client_group_client_api_url                  = "https://dt3-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url                    = "https://dt3-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                            = "https://dt3-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id                      = "2gptm2870hlo9ouq70poib8d5g"
  fineos_aws_iam_role_arn                             = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id                     = "12345"
  fineos_eligibility_feed_output_directory_path       = "s3://fin-somdev-data-import/DT3"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/DT3/dataexports"

  # These can be kept blank.
  eolwd_moveit_sftp_uri   = ""
  pfml_error_reports_path = "s3://massgov-pfml-cps-preview-agency-transfer/error-reports/outbound"

  dfml_project_manager_email_address     = "mass-pfml-payments-test-email@navapbc.com"
  pfml_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address        = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn    = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  dfml_business_operations_email_address = "mass-pfml-payments-test-email@navapbc.com"

  # TODO: Values from FINEOS.
  fineos_data_export_path       = "s3://fin-somdev-data-export/DT3/dataexports"
  fineos_adhoc_data_export_path = "s3://fin-somdev-data-export/DT3/dataExtracts/AdHocExtract"
  fineos_data_import_path       = "s3://fin-somdev-data-import/DT3/peiupdate"
  fineos_error_export_path      = "s3://fin-somdev-data-export/DT3/errorExtracts"
  fineos_report_export_path     = "s3://fin-somdev-data-export/DT3/reportExtract"

  pfml_fineos_inbound_path  = "s3://massgov-pfml-cps-preview-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path = "s3://massgov-pfml-cps-preview-agency-transfer/cps/outbound"

  payment_audit_report_outbound_folder_path = "s3://massgov-pfml-cps-preview-agency-transfer/audit/outbound"
  payment_audit_report_sent_folder_path     = "s3://massgov-pfml-cps-preview-agency-transfer/audit/sent"

  enable_register_admins_job = true

  enable_pub_automation_fineos           = true
  enable_pub_automation_create_pub_files = true
  enable_pub_automation_process_returns  = false
  enable_fineos_import_iaww              = true

  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-cps-preview/rmv_client_certificate-alAlg3"
  rmv_api_behavior                  = "partially_mocked"

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]

  # Hourly at :05 minutes past each hour
  dor_fineos_etl_schedule_expression_standard         = "cron(5 * * * ? *)"
  dor_fineos_etl_schedule_expression_daylight_savings = "cron(5 * * * ? *)"

  pdf_api_host                    = "http://localhost:5000"
  enable_generate_1099_pdf        = "0"
  generate_1099_max_files         = "1000"
  enable_merge_1099_pdf           = "0"
  enable_upload_1099_pdf          = "0"
  upload_max_files_to_fineos      = "10"
  enable_1099_testfile_generation = "0"
  irs_1099_correction_ind         = "0"

  enable_withholding_payments = "1"

  enable_pub_payments_copy_audit_report_schedule = true
}