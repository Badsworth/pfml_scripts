resource "aws_cloudwatch_metric_alarm" "sns_spending_limit" {
  for_each            = var.sns_spending_thresholds
  alarm_name          = "${local.prefix}sns-spending-limit-${each.key}"
  alarm_description   = "SNS spending ${each.key} threshold"
  comparison_operator = local.cloudwatch_comparison_operator
  evaluation_periods  = "1"
  metric_name         = "SMSMonthToDateSpentUSD"
  namespace           = local.namespace
  period              = local.default_aggregation_window
  statistic           = "Maximum"
  threshold           = each.value * var.sns_monthly_spend_limit
  treat_missing_data  = local.treat_missing_data
  alarm_actions       = [aws_sns_topic.sms_monthly_spend_limit.arn]
  ok_actions          = [aws_sns_topic.sms_monthly_spend_limit.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_failure_rate" {
  for_each            = var.sns_sms_failure_rate
  alarm_name          = "${local.prefix}sns-sms-failure-rate-${each.key}"
  alarm_description   = "SMS failure rate to phone numbers ${each.key} for 2 hours"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  datapoints_to_alarm = "1"
  metric_name         = "SMSSuccessRate"
  namespace           = local.namespace
  period              = local.one_hour
  statistic           = "Average"
  threshold           = each.value
  treat_missing_data  = local.treat_missing_data
  alarm_actions       = [aws_sns_topic.sms_messages_success_rate.arn]
  ok_actions          = [aws_sns_topic.sms_messages_success_rate.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_phone_carrier_unavailable" {
  for_each            = var.carrier_unavailable_period
  alarm_name          = "${local.prefix}sns-sms-phone-carrier-unavailable"
  alarm_description   = "More than ${local.phone_carrier_unavailable_threshold} SMS messages failed because Phone carrier unreachable/unavailable over ${each.value} seconds."
  comparison_operator = local.cloudwatch_comparison_operator
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_phone_carrier_unavailable.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_phone_carrier_unavailable.metric_transformation[0].namespace
  period              = each.value
  statistic           = local.statistic
  threshold           = local.phone_carrier_unavailable_threshold
  treat_missing_data  = local.treat_missing_data
  alarm_actions       = [aws_sns_topic.sms_phone_carrier_unavailable.arn]
  ok_actions          = [aws_sns_topic.sms_phone_carrier_unavailable.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_blocked_as_spam" {
  alarm_name          = "${local.prefix}sns-sms-blocked-as-spam"
  alarm_description   = "More than ${local.blocked_as_spam_threshold} SMS have been blocked as spam over 2 hours"
  comparison_operator = local.cloudwatch_comparison_operator
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_blocked_as_spam.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_blocked_as_spam.metric_transformation[0].namespace
  period              = local.two_hours
  statistic           = local.statistic
  threshold           = local.blocked_as_spam_threshold
  treat_missing_data  = local.treat_missing_data
  alarm_actions       = [aws_sns_topic.sms_blocked_as_spam.arn]
  ok_actions          = [aws_sns_topic.sms_blocked_as_spam.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_rate_exceeded" {
  alarm_name          = "${local.prefix}sns-sms-rate-exceeded"
  alarm_description   = "At least 1 SNS SMS rate exceeded error in 5 minutes"
  comparison_operator = local.cloudwatch_comparison_operator
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_rate_exceeded.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_rate_exceeded.metric_transformation[0].namespace
  period              = local.default_aggregation_window
  statistic           = local.statistic
  threshold           = 1
  treat_missing_data  = local.treat_missing_data
  alarm_actions       = [aws_sns_topic.sns_sms_rate_exceeded.arn]
  ok_actions          = [aws_sns_topic.sns_sms_rate_exceeded.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_mfa_delivery_time_exceeded" {
  alarm_name          = "${local.prefix}sns-mfa-delivery-time-exceeded"
  alarm_description   = "SNS MFA Delivery Time exceeded threshold"
  comparison_operator = local.cloudwatch_comparison_operator
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_mfa_delivery_time_exceeded.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_mfa_delivery_time_exceeded.metric_transformation[0].namespace
  period              = local.default_aggregation_window
  statistic           = local.statistic
  threshold           = 1
  treat_missing_data  = local.treat_missing_data
  alarm_actions       = [aws_sns_topic.sns_mfa_delivery_time_exceeded.arn]
  ok_actions          = [aws_sns_topic.sns_mfa_delivery_time_exceeded.arn]
}