# Defines an SNS topic for low-priority cloudwatch alerts.
resource "aws_sns_topic" "api-low-priority-alerts-topic" {
  name         = "api-low-priority-alerts-topic"
  display_name = "PFML API: Low Priority Alerts"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags["prod"]
  })
}

# Defines an SNS topic for high-priority cloudwatch alerts.
resource "aws_sns_topic" "api-high-priority-alerts-topic" {
  name         = "api-high-priority-alerts-topic"
  display_name = "PFML API: High Priority Alerts"
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
