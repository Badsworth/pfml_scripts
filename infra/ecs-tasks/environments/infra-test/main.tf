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
    bucket         = "massgov-pfml-infra-test-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name                  = "infra-test"
  service_docker_tag                = local.service_docker_tag
  vpc_id                            = data.aws_vpc.vpc.id
  app_subnet_ids                    = data.aws_subnet_ids.vpc_app.ids
  st_employer_update_limit          = 1500
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-stage/rmv_client_certificate-QlZaMl"

  # TODO: Fill this in once the Portal is deployed.
  cognito_user_pool_id = "us-east-1_8OEJk2XeD"

  # TODO: These values are provided by FINEOS.
  fineos_client_integration_services_api_url          = ""
  fineos_client_customer_api_url                      = ""
  fineos_client_group_client_api_url                  = ""
  fineos_client_wscomposer_api_url                    = ""
  fineos_client_oauth2_url                            = ""
  fineos_client_oauth2_client_id                      = ""
  fineos_aws_iam_role_arn                             = ""
  fineos_aws_iam_role_external_id                     = ""
  fineos_eligibility_feed_output_directory_path       = ""
  fineos_import_employee_updates_input_directory_path = ""

  # These can be kept blank.
  eolwd_moveit_sftp_uri   = ""
  pfml_error_reports_path = "s3://massgov-pfml-infra-test-agency-transfer/error-reports/outbound"

  dfml_project_manager_email_address     = "mass-pfml-payments-test-email@navapbc.com"
  pfml_email_address                     = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address        = "PFML_DoNotReply@eol.mass.gov"
  bounce_forwarding_email_address_arn    = "arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"
  dfml_business_operations_email_address = "mass-pfml-payments-test-email@navapbc.com"

  # TODO: Values from FINEOS.
  fineos_data_export_path       = ""
  fineos_adhoc_data_export_path = ""
  fineos_data_import_path       = ""
  fineos_error_export_path      = ""

  pfml_fineos_inbound_path  = "s3://massgov-pfml-infra-test-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path = "s3://massgov-pfml-infra-test-agency-transfer/cps/outbound"

  payment_audit_report_outbound_folder_path = "s3://massgov-pfml-infra-test-agency-transfer/audit/outbound"
  payment_audit_report_sent_folder_path     = "s3://massgov-pfml-infra-test-agency-transfer/audit/sent"

  enable_register_admins_job = true

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]

  pdf_api_host                    = "http://localhost:5000"
  enable_generate_1099_pdf        = "0"
  generate_1099_max_files         = "1000"
  enable_merge_1099_pdf           = "0"
  enable_upload_1099_pdf          = "0"
  upload_max_files_to_fineos      = "10"
  enable_1099_testfile_generation = "0"
  irs_1099_correction_ind         = "0"

  enable_employer_reimbursement_payments = "1"
}
