locals {
  environment_name = "prod"
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
    bucket         = "massgov-pfml-prod-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
  }
}

module "tasks" {
  source = "../../template"

  environment_name        = "prod"
  st_use_mock_dor_data    = false
  st_decrypt_dor_data     = true
  st_file_limit_specified = true
  service_docker_tag      = local.service_docker_tag
  vpc_id                  = data.aws_vpc.vpc.id
  app_subnet_ids          = data.aws_subnet_ids.vpc_app.ids

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

  eolwd_moveit_sftp_uri    = "sftp://DFML@transfer.eolwd.aws"
  ctr_moveit_incoming_path = "/DFML/Comptroller_Office/Incoming/nmmarsload"
  ctr_moveit_outgoing_path = "/DFML/Comptroller_Office/Outgoing/nmmarsload"
  ctr_moveit_archive_path  = "/DFML/Comptroller_Office/Archive"
  pfml_ctr_inbound_path    = "s3://massgov-pfml-prod-agency-transfer/ctr/inbound"
  pfml_ctr_outbound_path   = "s3://massgov-pfml-prod-agency-transfer/ctr/outbound"
  pfml_error_reports_path  = "s3://massgov-pfml-prod-agency-transfer/error-reports/outbound"
  pfml_voucher_output_path = "s3://massgov-pfml-prod-agency-transfer/payments/manual-payment-voucher"

  dfml_project_manager_email_address     = "kevin.bailey@mass.gov"
  pfml_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address        = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn    = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  ctr_gax_bievnt_email_address           = "Accounts.Payable@detma.org"
  ctr_vcc_bievnt_email_address           = "EOL-DL-DFML-GAXVCC_Confirmation@mass.gov"
  dfml_business_operations_email_address = "EOL-DL-DFML-GAXVCC_Confirmation@mass.gov"
  agency_reductions_email_address        = "EOL-DL-DFML-Agency-Reductions@mass.gov"

  ctr_data_mart_host     = "dua-fdm-wdb1.cs.govt.state.ma.us"
  ctr_data_mart_username = "SRV-LWD-DFML-PROD"

  fineos_data_export_path         = "s3://fin-somprod-data-export/PRD/dataexports"
  fineos_data_import_path         = "s3://fin-somprod-data-import/PRD/peiupdate"
  fineos_error_export_path        = "s3://fin-somprod-data-export/PRD/errorExtracts"
  pfml_fineos_inbound_path        = "s3://massgov-pfml-prod-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path       = "s3://massgov-pfml-prod-agency-transfer/cps/outbound"
  fineos_vendor_max_history_date  = "2021-01-11"
  fineos_payment_max_history_date = "2021-01-21"

  payment_audit_report_outbound_folder_path = "s3://massgov-pfml-prod-agency-transfer/audit/outbound"
  payment_audit_report_sent_folder_path     = "s3://massgov-pfml-prod-agency-transfer/audit/sent"

  enable_recurring_payments_schedule = true
  enable_register_admins_job         = true

  enable_pub_automation_fineos           = true
  enable_pub_automation_create_pub_files = true
  enable_pub_automation_process_returns  = true

  enable_reductions_send_claimant_lists_to_agencies_schedule        = true
  enable_reductions_retrieve_payment_lists_from_agencies_schedule   = true
  enable_reductions_send_wage_replacement_payments_to_dfml_schedule = true

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com", "EOL-DL-DFML-ITSUPPORT@MassMail.State.MA.US"]

  dor_fineos_etl_schedule_expression = "cron(30 0 * * ? *)" # Daily at 00:30 UTC [19:30 EST] [20:30 EDT]
}
