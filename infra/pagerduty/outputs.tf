output "low_priority_nr_integration_key" {
  value       = pagerduty_service_integration.newrelic_low_priority_notification.integration_key
  description = "this key is used to redirect low priority api events to the New Relic integration"
}

output "high_priority_nr_integration_key" {
  value       = pagerduty_service_integration.newrelic_high_priority_notification.integration_key
  description = "this key is used to redirect high priority api events to the New Relic integration"
}

output "low_priority_nr_portal_integration_key" {
  value       = pagerduty_service_integration.newrelic_low_priority_portal_notification.integration_key
  description = "this key is used to redirect low priority portal events to the New Relic integration"
}

output "high_priority_nr_portal_integration_key" {
  value       = pagerduty_service_integration.newrelic_high_priority_portal_notification.integration_key
  description = "this key is used to redirect high priority portal events to the New Relic integration"
}

output "low_priority_cloudwatch_integration_key" {
  value       = pagerduty_service_integration.cloudwatch_low_priority_notification.integration_key
  description = "this key is used to redirect low priority events to the Aws CloudWatch integration"
}

output "high_priority_cloudwatch_integration_key" {
  value       = pagerduty_service_integration.cloudwatch_high_priority_notification.integration_key
  description = "this key is used to redirect high priority events to the AWS CloudWatch integration"
}
output "security_scan_notification_channel_integration_key" {
  value       = pagerduty_service_integration.security_scan_notification_channel.integration_key
  description = "this key is used to redirect Security and Bandit events to the Events Api integration"
}