provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-stage-env-mgmt"
    key            = "terraform/ecs-tasks.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

module "tasks" {
  source = "../../template"

  environment_name   = "stage"
  service_docker_tag = local.service_docker_tag
  vpc_id             = data.aws_vpc.vpc.id
  app_subnet_ids     = data.aws_subnet_ids.vpc_app.ids

  cognito_user_pool_id                       = "us-east-1_HpL4XslLg"
  fineos_client_integration_services_api_url = "https://idt-api.masspfml.fineos.com/integration-services/"
  fineos_client_customer_api_url             = "https://idt-api.masspfml.fineos.com/customerapi/"
  fineos_client_group_client_api_url         = "https://idt-api.masspfml.fineos.com/groupclientapi/"
  fineos_client_wscomposer_api_url           = "https://idt-api.masspfml.fineos.com/integration-services/wscomposer/"
  fineos_client_oauth2_url                   = "https://idt-api.masspfml.fineos.com/oauth2/token"
  fineos_client_oauth2_client_id             = "1fa281uto9tjuqtm21jle7loam"

  fineos_aws_iam_role_arn         = "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B"
  fineos_aws_iam_role_external_id = "12345"

  fineos_eligibility_feed_output_directory_path       = "s3://fin-somdev-data-import/IDT"
  fineos_import_employee_updates_input_directory_path = "s3://fin-somdev-data-export/IDT/dataexports"

  payments_fineos_data_export_path   = "s3://fin-somedev-data-export/IDT/dataexports"
  payments_pfml_fineos_inbound_path  = "s3://massgov-pfml-stage-agency-transfer/cps/inbound"
  payments_fineos_data_import_path   = "s3://fin-somedev-data-import/IDT/peiupdate"
  payments_pfml_fineos_outbound_path = "s3://massgov-pfml-stage-agency-transfer/cps/outbound"
  payments_ctr_moveit_incoming_path  = "sftp://TBD"
  payments_ctr_moveit_archive_path   = "sftp://TBD"
  payments_pfml_ctr_inbound_path     = "s3://massgov-pfml-stage-agency-transfer/ctr/inbound"
  payments_ctr_moveit_outgoing_path  = "sftp://TBD"
  payments_pfml_ctr_outbound_path    = "s3://massgov-pfml-stage-agency-transfer/ctr/outbound"

  enable_recurring_payments_schedule = false

  logging_level = "massgov.pfml.fineos.fineos_client=DEBUG"

  payments_gax_bievnt_email       = ""
  pfml_email_address              = "noreplypfml@mass.gov"
  bounce_forwarding_email_address = "noreplypfml@mass.gov"
}
