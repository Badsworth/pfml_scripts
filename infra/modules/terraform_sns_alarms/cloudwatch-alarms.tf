resource "aws_cloudwatch_metric_alarm" "sns_spending_limit_exceeded" {
  alarm_name          = "sns-spending-limit-exceeded"
  alarm_description   = "SNS spending reached/exceeded 100% of limit this month"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "SMSMonthToDateSpentUSD"
  namespace           = "AWS/SNS"
  period              = "300"
  statistic           = "Maximum"
  threshold           = var.sns_monthly_spend_limit
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.sms_monthly_spend_limit.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_spending_critical" {
  alarm_name          = "sns-spending-critical"
  alarm_description   = "SNS spending reached 90% of limit this month"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "SMSMonthToDateSpentUSD"
  namespace           = "AWS/SNS"
  period              = "300"
  statistic           = "Maximum"
  threshold           = 0.9 * var.sns_monthly_spend_limit
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.sms_monthly_spend_limit.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_spending_warning" {
  alarm_name          = "sns-spending-warning"
  alarm_description   = "SNS spending reached 80% of limit this month"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "SMSMonthToDateSpentUSD"
  namespace           = "AWS/SNS"
  period              = "300"
  statistic           = "Maximum"
  threshold           = 0.8 * var.sns_monthly_spend_limit
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.sms_monthly_spend_limit.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_spending_information" {
  alarm_name          = "sns-spending-information"
  alarm_description   = "SNS spending reached 50% of limit this month"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "SMSMonthToDateSpentUSD"
  namespace           = "AWS/SNS"
  period              = "300"
  statistic           = "Maximum"
  threshold           = 0.5 * var.sns_monthly_spend_limit
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.sms_monthly_spend_limit.arn]
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_failure_rate_critical" {
  alarm_name          = "sns-sms-failure-rate-critical"
  alarm_description   = "SMS success rate to phone numbers is below 50% over 2 consecutive periods of 12 hours"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  datapoints_to_alarm = "2"
  metric_name         = "SMSSuccessRate"
  namespace           = "AWS/SNS"
  period              = 60 * 60 * 12
  statistic           = "Average"
  threshold           = 0.5
  alarm_actions       = [aws_sns_topic.sms_messages_success_rate.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_failure_rate_warning" {
  alarm_name          = "sns-sms-failure-rate-warning"
  alarm_description   = "SMS success rate to phone numbers is below 75% over 2 consecutive periods of 12 hours"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  datapoints_to_alarm = "2"
  metric_name         = "SMSSuccessRate"
  namespace           = "AWS/SNS"
  period              = 60 * 60 * 12
  statistic           = "Average"
  threshold           = 0.75
  alarm_actions       = [aws_sns_topic.sms_messages_success_rate.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_phone_carrier_unavailable_warning" {
  alarm_name          = "sns-sms-phone-carrier-unavailable-warning"
  alarm_description   = "More than 10 SMS failed because a phone carrier is unavailable over 3 hours"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_phone_carrier_unavailable.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_phone_carrier_unavailable.metric_transformation[0].namespace
  period              = 60 * 60 * 3
  statistic           = "Sum"
  threshold           = 1
  alarm_actions       = [aws_sns_topic.sms_phone_carrier_unavailable.arn]
  treat_missing_data  = "notBreaching"
}

# how can we exclude delivery.destination = '12064350128' this number is used for testing?
# is this necessary given the evaluation_periods?
resource "aws_cloudwatch_metric_alarm" "sns_sms_phone_carrier_unavailable_critical" {
  alarm_name          = "sns-sms-phone-carrier-unavailable-critical"
  alarm_description   = "More than 10 SMS failed because a phone carrier is unavailable over 6 hours"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_phone_carrier_unavailable.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_phone_carrier_unavailable.metric_transformation[0].namespace
  period              = 60 * 60 * 6
  statistic           = "Sum"
  threshold           = 1
  alarm_actions       = [aws_sns_topic.sms_phone_carrier_unavailable.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_blocked_as_spam_warning" {
  alarm_name          = "sns-sms-blocked-as-spam-warning"
  alarm_description   = "More than 10 SMS have been blocked as spam over 12 hours"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_blocked_as_spam.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_blocked_as_spam.metric_transformation[0].namespace
  period              = 60 * 60 * 12
  statistic           = "Sum"
  threshold           = 10
  alarm_actions       = [aws_sns_topic.sms_blocked_as_spam.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "sns_sms_rate_exceeded" {
  alarm_name          = "sns-sms-rate-exceeded"
  alarm_description   = "At least 1 SNS SMS rate exceeded error in 5 minutes"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = aws_cloudwatch_log_metric_filter.sns_sms_rate_exceeded.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.sns_sms_rate_exceeded.metric_transformation[0].namespace
  period              = 60 * 5
  statistic           = "Sum"
  threshold           = 1
  alarm_actions       = [aws_sns_topic.sns_sms_rate_exceeded.arn]
  treat_missing_data  = "notBreaching"
}
