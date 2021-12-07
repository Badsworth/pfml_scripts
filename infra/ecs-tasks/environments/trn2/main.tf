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
    bucket         = "massgov-pfml-trn2-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name         = "trn2"
  service_docker_tag       = local.service_docker_tag
  vpc_id                   = data.aws_vpc.vpc.id
  app_subnet_ids           = data.aws_subnet_ids.vpc_app.ids
  st_employer_update_limit = 1500

  # TODO: Fill this in once the Portal is deployed.
  cognito_user_pool_id = "us-east-1_oxOGrdAe8"

  # TODO: These values are provided by FINEOS.
  fineos_client_integration_services_api_url          = ""
  fineos_client_customer_api_url                      = ""
  fineos_client_group_client_api_url                  = ""
  fineos_client_wscomposer_api_url                    = ""
  fineos_client_oauth2_url                            = ""
  fineos_client_oauth2_client_id                      = "2e9vsuq808h3tu4rf9tr1efuh5"
  fineos_aws_iam_role_arn                             = ""
  fineos_aws_iam_role_external_id                     = ""
  fineos_eligibility_feed_output_directory_path       = ""
  fineos_import_employee_updates_input_directory_path = ""

  # These can be kept blank.
  eolwd_moveit_sftp_uri   = ""
  pfml_error_reports_path = "s3://massgov-pfml-trn2-agency-transfer/error-reports/outbound"

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

  pfml_fineos_inbound_path  = "s3://massgov-pfml-trn2-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path = "s3://massgov-pfml-trn2-agency-transfer/cps/outbound"

  payment_audit_report_outbound_folder_path = "s3://massgov-pfml-trn2-agency-transfer/audit/outbound"
  payment_audit_report_sent_folder_path     = "s3://massgov-pfml-trn2-agency-transfer/audit/sent"

  enable_register_admins_job = true

  rmv_client_base_url               = "https://atlas-staging-gateway.massdot.state.ma.us/vs"
  rmv_client_certificate_binary_arn = "arn:aws:secretsmanager:us-east-1:498823821309:secret:/service/pfml-api-trn2/rmv_client_certificate-D5TPeE"
  rmv_api_behavior                  = "partially_mocked"

  task_failure_email_address_list = ["mass-pfml-api-low-priority@navapbc.pagerduty.com"]

  pdf_api_host             = "https://localhost:5001"
  enable_generate_1099_pdf = "1"
  enable_merge_1099_pdf    = "1"
}
