data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_ssm_parameter" "newrelic-api-key" {
  name = "/admin/pfml-api/newrelic-api-key"
}

data "aws_ssm_parameter" "newrelic-admin-api-key" {
  name = "/admin/pfml-api/newrelic-admin-api-key"
}

module "constants" {
  source = "../../constants"
}

provider "newrelic" {
  region        = "US"
  account_id    = module.constants.newrelic_account_id
  api_key       = data.aws_ssm_parameter.newrelic-api-key.value
  admin_api_key = data.aws_ssm_parameter.newrelic-admin-api-key.value
}

# new relic account id and key are duplicated in
#  alarms_api/main.tf
#  alarms_portal/main.tf
#  email_bounce/main.tf
#  newrelic_baseline_error_rate/main.tf
#  add to backlog
locals {
  app_name = "aws-sns"

  low_priority_channel_key     = var.low_priority_nr_integration_key
  high_priority_channel_key    = var.high_priority_nr_integration_key
  violation_time_limit_seconds = 86400 # 24 hours
  default_aggregation_period   = 300   # 5 minutes
  sns_failure_log_group_name   = "sns/${data.aws_region.current.name}/${data.aws_caller_identity.current.account_id}/DirectPublishToPhoneNumber/Failure"
}