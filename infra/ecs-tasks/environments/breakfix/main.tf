locals {
  environment_name = "breakfix"
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
    bucket         = "massgov-pfml-breakfix-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name         = "breakfix"
  st_decrypt_dor_data      = false
  st_use_mock_dor_data     = false
  st_file_limit_specified  = true
  st_employer_update_limit = 250
  service_docker_tag       = local.service_docker_tag
  vpc_id                   = data.aws_vpc.vpc.id
  app_subnet_ids           = data.aws_subnet_ids.vpc_app.ids

  cognito_user_pool_id                       = "us-east-1_Bi6tPV5hz"
  fineos_client_customer_api_url             = "https://pfx-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url = "https://pfx-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url         = "https://pfx-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url           = "https://pfx-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_wscomposer_user_id           = "OASIS"
  fineos_client_oauth2_url                   = "https://pfx-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "470dvu60ij99vpgsm8dug3nuhg"

  fineos_aws_iam_role_arn         = "arn:aws:iam::016390658835:role/sompre-IAMRoles-CustomerAccountAccessRole-S0EP9ABIA02Z"
  fineos_aws_iam_role_external_id = "8jFBtjr4UA@"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-sompre-data-import/PFX/"
  fineos_import_employee_updates_input_directory_path = "s3://fin-sompre-data-export/PFX/dataexports"

  # These can be kept blank.
  eolwd_moveit_sftp_uri    = ""
  ctr_moveit_incoming_path = ""
  ctr_moveit_outgoing_path = ""
  ctr_moveit_archive_path  = ""
  pfml_ctr_inbound_path    = "s3://massgov-pfml-breakfix-agency-transfer/ctr/inbound"
  pfml_ctr_outbound_path   = "s3://massgov-pfml-breakfix-agency-transfer/ctr/outbound"
  pfml_error_reports_path  = "s3://massgov-pfml-breakfix-agency-transfer/error-reports/outbound"
  pfml_voucher_output_path = "s3://massgov-pfml-breakfix-agency-transfer/payments/manual-payment-voucher"

  dfml_project_manager_email_address     = "mass-pfml-payments-test-email@navapbc.com"
  pfml_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address        = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn    = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  ctr_gax_bievnt_email_address           = "mass-pfml-payments-test-email@navapbc.com"
  ctr_vcc_bievnt_email_address           = "mass-pfml-payments-test-email@navapbc.com"
  dfml_business_operations_email_address = "mass-pfml-payments-test-email@navapbc.com"
  agency_reductions_email_address        = "mass-pfml-payments-test-email@navapbc.com"

  # These can be kept blank.
  ctr_data_mart_host     = ""
  ctr_data_mart_username = ""

  fineos_data_export_path   = "s3://fin-sompre-data-export/PFX/dataexports"
  fineos_data_import_path   = "s3://fin-sompre-data-import/PFX/peiupdate"
  fineos_error_export_path  = "s3://fin-sompre-data-export/PFX/errorExtracts"
  fineos_report_export_path = "s3://fin-sompre-data-export/PFX/reportExtracts"
  pfml_fineos_inbound_path  = "s3://massgov-pfml-breakfix-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path = "s3://massgov-pfml-breakfix-agency-transfer/cps/outbound"

  # TODO: Not sure what these should be configured to by default.
  fineos_vendor_max_history_date  = "2021-01-11"
  fineos_payment_max_history_date = "2021-01-21"

  payment_audit_report_outbound_folder_path = "s3://massgov-pfml-breakfix-agency-transfer/audit/outbound"
  payment_audit_report_sent_folder_path     = "s3://massgov-pfml-breakfix-agency-transfer/audit/sent"

  enable_recurring_payments_schedule = false
  enable_register_admins_job         = true

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]

  dor_fineos_etl_schedule_expression = "cron(5 * * * ? *)" # Hourly at :05 minutes past each hour
}
