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

locals {
  low_priority_channel_key            = var.low_priority_nr_integration_key
  high_priority_channel_key           = var.high_priority_nr_integration_key
  violation_time_limit_seconds        = 86400 # 24 hours
  default_aggregation_window          = 300   # 5 minutes
  mfa_user_response_time              = 5000  # 5 seconds
  mfa_sns_delivery_time               = 1000  # 1 second
  one_hour                            = local.default_aggregation_window * 12
  two_hours                           = local.one_hour * 2
  phone_carrier_unavailable_threshold = 25
  blocked_as_spam_threshold           = 10
  sns_log_group_name                  = "sns/${data.aws_region.current.name}/${data.aws_caller_identity.current.account_id}/DirectPublishToPhoneNumber"
  sns_failure_log_group_name          = "sns/${data.aws_region.current.name}/${data.aws_caller_identity.current.account_id}/DirectPublishToPhoneNumber/Failure"
}