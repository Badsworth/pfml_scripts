provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

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

  environment_name   = "prod"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id
  app_subnet_ids     = data.aws_subnet_ids.vpc_app.ids

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
  ctr_moveit_incoming_path = "Comptroller_Office/Incoming/nmmarsload"
  ctr_moveit_outgoing_path = "Comptroller_Office/Outgoing/nmmarsload"
  ctr_moveit_archive_path  = "Comptroller_Office/Archive"
  pfml_ctr_inbound_path    = "s3://massgov-pfml-prod-agency-transfer/ctr/inbound"
  pfml_ctr_outbound_path   = "s3://massgov-pfml-prod-agency-transfer/ctr/outbound"
  pfml_error_reports_path  = "s3://massgov-pfml-prod-agency-transfer/error-reports/outbound"

  pfml_email_address                     = "noreplypfml@mass.gov"
  bounce_forwarding_email_address        = "noreplypfml@mass.gov"
  ctr_gax_bievnt_email_address           = "Accounts.Payable@detma.org"
  ctr_vcc_bievnt_email_address           = "EOL-DL-DFML-GAXVCC_Confirmation@mass.gov"
  dfml_business_operations_email_address = "EOL-DL-DFML-GAXVCC_Confirmation@mass.gov"

  ctr_data_mart_host     = "dua-fdm-wdb1.cs.govt.state.ma.us"
  ctr_data_mart_username = "SRV-LWD-DFML-PROD"

  fineos_data_export_path         = "s3://fin-somprod-data-export/PRD/dataexports"
  fineos_data_import_path         = "s3://fin-somprod-data-import/PRD/peiupdate"
  pfml_fineos_inbound_path        = "s3://massgov-pfml-prod-agency-transfer/cps/inbound"
  pfml_fineos_outbound_path       = "s3://massgov-pfml-prod-agency-transfer/cps/outbound"
  fineos_vendor_max_history_date  = "2021-01-11"
  fineos_payment_max_history_date = "2021-01-21"

  enable_recurring_payments_schedule = false
  enable_register_admins_job         = true
}
