output "sns_spending_critical_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.sns_spending_critical.arn
}

output "sms_monthly_spend_limit_topic_arn" {
  value = aws_sns_topic.sms_monthly_spend_limit.arn
}

output "sms_messages_success_rate_topic_arn" {
  value = aws_sns_topic.sms_messages_success_rate.arn
}

output "sms_phone_carrier_unavailable_topic_arn" {
  value = aws_sns_topic.sms_phone_carrier_unavailable.arn
}

output "sms_blocked_as_spam_topic_arn" {
  value = aws_sns_topic.sms_blocked_as_spam.arn
}

output "sns_sms_rate_exceeded_topic_arn" {
  value = aws_sns_topic.sns_sms_rate_exceeded.arn
}