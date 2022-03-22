locals {
  environment_name = "prod"
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
    bucket         = "massgov-pfml-prod-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
  }
}

module "tasks" {
  source = "../../template"

  environment_name              = "prod"
  st_use_mock_dor_data          = false
  st_decrypt_dor_data           = true
  st_file_limit_specified       = true
  st_employer_update_limit      = 1500
  service_docker_tag            = local.service_docker_tag
  vpc_id                        = data.aws_vpc.vpc.id
  app_subnet_ids                = data.aws_subnet_ids.vpc_app.ids
  enforce_execute_sql_read_only = true

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

  eolwd_moveit_sftp_uri   = "sftp://DFML@transfer.eolwd.aws"
  pfml_error_reports_path = "s3://massgov-pfml-prod-agency-transfer/error-reports/outbound"

  dfml_project_manager_email_address     = "kevin.bailey@mass.gov"
  pfml_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address        = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn    = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  dfml_business_operations_email_address = "EOL-DL-DFML-GAXVCC_Confirmation@mass.gov"
  agency_reductions_email_address        = "EOL-DL-DFML-Agency-Reductions@mass.gov"

  fineos_data_export_path       = "s3://fin-somprod-data-export/PRD/dataexports"
  fineos_adhoc_data_export_path = "s3://fin-somprod-data-export/PRD/dataExtracts/AdHocExtract"
  fineos_data_import_path       = "s3://fin-somprod-data-import/PRD/peiupdate"
  fineos_error_export_path      = "s3://fin-somprod-data-export/PRD/errorExtracts"
  fineos_report_export_path     = "s3://fin-somprod-data-export/PRD/reportExtract"
  pfml_fineos_inbound_path      = "s3://massgov-pfml-prod-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path     = "s3://massgov-pfml-prod-agency-transfer/cps/outbound"

  payment_audit_report_outbound_folder_path = "s3://massgov-pfml-prod-agency-transfer/audit/outbound"
  payment_audit_report_sent_folder_path     = "s3://massgov-pfml-prod-agency-transfer/audit/sent"

  enable_register_admins_job = true

  enable_pub_automation_fineos                     = true
  enable_pub_automation_create_pub_files           = true
  enable_pub_automation_process_returns            = true
  enable_fineos_import_iaww                        = true
  enable_standalone_fineos_import_employee_updates = true

  enable_reductions_send_claimant_lists_to_agencies_schedule = true
  enable_reductions_process_agency_data_schedule             = true

  rmv_client_base_url               = "https://atlas-gateway.massdot.state.ma.us"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-prod/rmv_client_certificate-Mo2HJu"
  rmv_api_behavior                  = "not_mocked"

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com", "EOL-DL-DFML-ITSUPPORT@MassMail.State.MA.US"]

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
}
