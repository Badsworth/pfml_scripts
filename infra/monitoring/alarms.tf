# Terraform configuration for any alarm that's stored in New Relic.

locals {
  environments = ["test", "stage", "prod", "performance", "training", "uat"]
}

module "alarms_api" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_api"

  environment_name                 = each.key
  low_priority_nr_integration_key  = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  high_priority_nr_integration_key = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
  warning_alert_sns_topic_arn      = aws_sns_topic.api-low-priority-alerts-topic.arn
  critical_alert_sns_topic_arn     = each.key == "prod" ? aws_sns_topic.api-high-priority-alerts-topic.arn : aws_sns_topic.api-low-priority-alerts-topic.arn
  enable_alarm_api_cpu             = each.key != "test"
  enable_alarm_api_ram             = each.key != "test"
}

module "alarms_portal" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_portal"

  environment_name                        = each.key
  low_priority_nr_portal_integration_key  = pagerduty_service_integration.newrelic_low_priority_portal_notification.integration_key
  high_priority_nr_portal_integration_key = pagerduty_service_integration.newrelic_high_priority_portal_notification.integration_key
}

module "email_bounce" {
  source = "../modules/email_bounce"

  low_priority_nr_integration_key  = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  high_priority_nr_integration_key = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
}
