provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name   = "test"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id
  app_subnet_ids     = data.aws_subnet_ids.vpc_app.ids

  cognito_user_pool_id                       = "us-east-1_HhQSLYSIe"
  fineos_client_integration_services_api_url = "https://dt2-api.masspfml.fineos.com/integration-services/"
  fineos_client_group_client_api_url         = "https://dt2-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_customer_api_url             = "https://dt2-api.masspfml.fineos.com/customerapi/"
  fineos_client_wscomposer_api_url           = "https://dt2-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                   = "https://dt2-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "1ral5e957i0l9shul52bhk0037"

  fineos_aws_iam_role_arn         = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id = "12345"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-somdev-data-import/DT2"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/DT2/dataexports"
  logging_level                                       = "massgov.pfml.fineos.fineos_client=DEBUG"

  eolwd_moveit_sftp_uri    = ""
  ctr_moveit_incoming_path = ""
  ctr_moveit_outgoing_path = ""
  ctr_moveit_archive_path  = ""
  pfml_ctr_inbound_path    = "s3://massgov-pfml-test-agency-transfer/ctr/inbound"
  pfml_ctr_outbound_path   = "s3://massgov-pfml-test-agency-transfer/ctr/outbound"

  pfml_email_address                     = "noreplypfml@mass.gov"
  bounce_forwarding_email_address        = "noreplypfml@mass.gov"
  ctr_gax_bievnt_email_address           = "mass-pfml-payments-test-email@navapbc.com"
  ctr_vcc_bievnt_email_address           = "mass-pfml-payments-test-email@navapbc.com"
  dfml_business_operations_email_address = "mass-pfml-payments-test-email@navapbc.com"

  ctr_data_mart_host     = ""
  ctr_data_mart_username = ""

  fineos_data_export_path   = "s3://fin-somdev-data-export/DT2/dataexports"
  fineos_data_import_path   = "s3://fin-somdev-data-import/DT2/peiupdate"
  pfml_fineos_inbound_path  = "s3://massgov-pfml-test-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path = "s3://massgov-pfml-test-agency-transfer/cps/outbound"

  enable_recurring_payments_schedule = false
}
