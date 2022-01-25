# The DirectPublishToPhoneNumber is created automatically by SNS
# https://aws.amazon.com/premiumsupport/knowledge-center/monitor-sns-texts-cloudwatch/
resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_sns_sms_success" {
  name            = "nr_lambda_sns_sms_success"
  log_group_name  = "sns/${data.aws_region.current.name}/${data.aws_caller_identity.current.account_id}/DirectPublishToPhoneNumber"
  filter_pattern  = ""
  destination_arn = module.constants.newrelic_log_ingestion_arn
}

# The DirectPublishToPhoneNumber/Failure is created automatically by SNS
# https://aws.amazon.com/premiumsupport/knowledge-center/monitor-sns-texts-cloudwatch/
resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_sns_sms_failure" {
  name            = "nr_lambda_sns_sms_failure"
  log_group_name  = local.sns_failure_log_group_name
  filter_pattern  = ""
  destination_arn = module.constants.newrelic_log_ingestion_arn
}