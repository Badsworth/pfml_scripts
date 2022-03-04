# Defines an SNS topic for low-priority cloudwatch alerts.
resource "aws_sns_topic" "api-low-priority-alerts-topic" {
  name              = "api-low-priority-alerts-topic"
  display_name      = "PFML API: Low Priority Alerts"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags["prod"]
  })
}

# Defines an SNS topic for high-priority cloudwatch alerts.
resource "aws_sns_topic" "api-high-priority-alerts-topic" {
  name              = "api-high-priority-alerts-topic"
  display_name      = "PFML API: High Priority Alerts"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags["prod"]
  })
}

# Defines SNS topic subscriptions for AWS Cloudwatch --> Pagerduty notifications.
resource "aws_sns_topic_subscription" "low-priority" {
  topic_arn              = aws_sns_topic.api-low-priority-alerts-topic.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_low_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "high-priority" {
  topic_arn              = aws_sns_topic.api-high-priority-alerts-topic.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_monthly_spend_limit" {
  topic_arn              = module.sns_alarms.sms_monthly_spend_limit_topic_arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_messages_success_rate" {
  topic_arn              = module.sns_alarms.sms_messages_success_rate_topic_arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_phone_carrier_unavailable" {
  topic_arn              = module.sns_alarms.sms_phone_carrier_unavailable_topic_arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sms_blocked_as_spam" {
  topic_arn              = module.sns_alarms.sms_blocked_as_spam_topic_arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_low_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "sns_sms_rate_exceeded" {
  topic_arn              = module.sns_alarms.sns_sms_rate_exceeded_topic_arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key}/enqueue"
  endpoint_auto_confirms = true
}
