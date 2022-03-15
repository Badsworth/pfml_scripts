resource "aws_sns_topic_subscription" "sms_monthly_spend_limit" {
  topic_arn              = aws_sns_topic.sms_monthly_spend_limit.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${var.high_priority_pager_duty_integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_messages_success_rate" {
  topic_arn              = aws_sns_topic.sms_messages_success_rate.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${var.high_priority_pager_duty_integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_phone_carrier_unavailable" {
  topic_arn              = aws_sns_topic.sms_phone_carrier_unavailable.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${var.high_priority_pager_duty_integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_blocked_as_spam" {
  topic_arn              = aws_sns_topic.sms_blocked_as_spam.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${var.low_priority_pager_duty_integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sns_sms_rate_exceeded" {
  topic_arn              = aws_sns_topic.sns_sms_rate_exceeded.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${var.high_priority_pager_duty_integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sns_mfa_delivery_time_exceeded" {
  topic_arn              = aws_sns_topic.sns_mfa_delivery_time_exceeded.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${var.low_priority_pager_duty_integration_key}/enqueue"
  endpoint_auto_confirms = true
}
