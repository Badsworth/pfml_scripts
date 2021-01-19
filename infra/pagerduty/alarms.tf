# Terraform configuration for any alarm that's stored in New Relic.

locals {
  environments = ["test", "stage", "prod", "performance", "training"]
}

module "alarms_api" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_api"

  environment_name                         = each.key
  low_priority_nr_integration_key          = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  high_priority_nr_integration_key         = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
  low_priority_cloudwatch_integration_key  = pagerduty_service_integration.cloudwatch_low_priority_notification.integration_key
  high_priority_cloudwatch_integration_key = pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key
  enable_alarm_api_cpu                     = each.key != "test"
  enable_alarm_api_ram                     = each.key != "test"

}

module "alarms_portal" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_portal"

  environment_name                        = each.key
  low_priority_nr_portal_integration_key  = pagerduty_service_integration.newrelic_low_priority_portal_notification.integration_key
  high_priority_nr_portal_integration_key = pagerduty_service_integration.newrelic_high_priority_portal_notification.integration_key
}
