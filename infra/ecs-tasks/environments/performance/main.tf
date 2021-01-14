provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-performance-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name   = "performance"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id
  app_subnet_ids     = data.aws_subnet_ids.vpc_app.ids

  cognito_user_pool_id                       = "us-east-1_0jv6SlemT"
  fineos_client_customer_api_url             = "https://perf-api.masspfml.fineos.com/customerapi/"
  fineos_client_integration_services_api_url = "https://perf-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url         = "https://perf-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url           = "https://perf-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                   = "https://perf-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "5u0hcdodd6vt5bfa6p2u6ij13d"

  fineos_aws_iam_role_arn         = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id = "12345"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-somdev-data-import/PERF"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/PERF/dataexports"
  logging_level                                       = "massgov.pfml.fineos.fineos_client=DEBUG"

  eolwd_moveit_sftp_uri    = "sftp://DFML@transferwebtest.eolwd.aws"
  ctr_moveit_incoming_path = "Comptroller_Office/Incoming/nmmarsload"
  ctr_moveit_outgoing_path = "Comptroller_Office/Outgoing/nmmarsload"
  ctr_moveit_archive_path  = "Comptroller_Office/Archive"
  pfml_ctr_inbound_path    = "s3://massgov-pfml-performance-agency-transfer/ctr/inbound"
  pfml_ctr_outbound_path   = "s3://massgov-pfml-performance-agency-transfer/ctr/outbound"
  pfml_error_reports_path  = "s3://massgov-pfml-performance-agency-transfer/error-reports/outbound"

  pfml_email_address                     = "noreplypfml@mass.gov"
  bounce_forwarding_email_address        = "noreplypfml@mass.gov"
  bounce_forwarding_email_address_arn    = "arn:aws:ses:us-east-1:498823821309:identity/noreplypfml@mass.gov"
  ctr_gax_bievnt_email_address           = "mass-pfml-payments-test-email@navapbc.com"
  ctr_vcc_bievnt_email_address           = "mass-pfml-payments-test-email@navapbc.com"
  dfml_business_operations_email_address = "mass-pfml-payments-test-email@navapbc.com"

  ctr_data_mart_host     = "duaua-fdm-wdb1.cs.govt.state.ma.us"
  ctr_data_mart_username = "SRV-LWD-DFML-NONPROD"

  fineos_data_export_path         = "s3://fin-somdev-data-export/PERF/dataexports"
  fineos_data_import_path         = "s3://fin-somdev-data-import/PERF/peiupdate"
  pfml_fineos_inbound_path        = "s3://massgov-pfml-performance-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path       = "s3://massgov-pfml-performance-agency-transfer/cps/outbound"
  fineos_vendor_max_history_date  = "2021-01-09"
  fineos_payment_max_history_date = "2021-01-21"

  enable_recurring_payments_schedule = false
  enable_register_admins_job         = false
}
