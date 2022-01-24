resource "aws_cloudwatch_log_metric_filter" "sns_sms_blocked_as_spam" {
  name           = "SmsBlockedAsSpam"
  pattern        = "{ $.delivery.providerResponse = \"Blocked as spam by phone carrier\" }"
  log_group_name = local.sns_failure_log_group_name

  metric_transformation {
    name          = "SmsBlockedAsSpam"
    namespace     = "LogMetrics"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "sns_sms_phone_carrier_unavailable" {
  name           = "SmsPhoneCarrierUnavailable"
  pattern        = "{ $.delivery.providerResponse = \"Phone carrier is currently unreachable/unavailable\" }"
  log_group_name = local.sns_failure_log_group_name

  metric_transformation {
    name          = "SmsPhoneCarrierUnavailable"
    namespace     = "LogMetrics"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "sns_sms_rate_exceeded" {
  name           = "SmsRateExceeded"
  pattern        = "{ $.delivery.providerResponse = \"Rate exceeded\" }"
  log_group_name = local.sns_failure_log_group_name

  metric_transformation {
    name          = "SmsRateExceeded"
    namespace     = "LogMetrics"
    value         = "1"
    default_value = "0"
  }
}