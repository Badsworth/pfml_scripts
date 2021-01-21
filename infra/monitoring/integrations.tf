# Email Integrations for the Portal and API
#########
resource "pagerduty_service_integration" "mass_pfml_api_low_priority_email" {
  name              = "Low Priority Email for Mass PFML API"
  type              = "generic_email_inbound_integration"
  integration_email = "mass-pfml-api-low-priority@navapbc.pagerduty.com"
  service           = pagerduty_service.mass_pfml_api_low_priority.id
}

resource "pagerduty_service_integration" "mass_pfml_api_high_priority_email" {
  name              = "High Priority Email for Mass PFML API"
  type              = "generic_email_inbound_integration"
  integration_email = "mass-pfml-api-high-priority@navapbc.pagerduty.com"
  service           = pagerduty_service.mass_pfml_api_high_priority.id
}

resource "pagerduty_service_integration" "mass_pfml_portal_low_priority_email" {
  name              = "Low Priority Email for Mass PFML Portal"
  type              = "generic_email_inbound_integration"
  integration_email = "mass-pfml-portal-low-priority@navapbc.pagerduty.com"
  service           = pagerduty_service.mass_pfml_portal_low_priority.id
}

resource "pagerduty_service_integration" "mass_pfml_portal_high_priority_email" {
  name              = "High Priority Email for Mass PFML Portal"
  type              = "generic_email_inbound_integration"
  integration_email = "mass-pfml-portal-high-priority@navapbc.pagerduty.com"
  service           = pagerduty_service.mass_pfml_portal_high_priority.id
}
# PagerDuty Intergrations for NewRelic
data "pagerduty_vendor" "newrelic" {
  name = "New Relic"
}
resource "pagerduty_service_integration" "newrelic_low_priority_notification" {
  name    = "Low Priority Notification for New Relic"
  service = pagerduty_service.mass_pfml_api_low_priority.id
  vendor  = data.pagerduty_vendor.newrelic.id
}

resource "pagerduty_service_integration" "newrelic_high_priority_portal_notification" {
  name    = "High Priority Notification for New Relic"
  service = pagerduty_service.mass_pfml_portal_high_priority.id
  vendor  = data.pagerduty_vendor.newrelic.id
}

resource "pagerduty_service_integration" "newrelic_low_priority_portal_notification" {
  name    = "Low Priority Notification for New Relic"
  service = pagerduty_service.mass_pfml_portal_low_priority.id
  vendor  = data.pagerduty_vendor.newrelic.id
}

resource "pagerduty_service_integration" "newrelic_high_priority_notification" {
  name    = "High Priority Notification for New Relic"
  service = pagerduty_service.mass_pfml_api_high_priority.id
  vendor  = data.pagerduty_vendor.newrelic.id
}
# Integration for Cloudwatch
data "pagerduty_vendor" "cloudwatch" {
  name = "Amazon CloudWatch"
}

resource "pagerduty_service_integration" "cloudwatch_high_priority_notification" {
  name    = "High Priority Notification for AWS Cloudwatch"
  service = pagerduty_service.mass_pfml_api_high_priority.id
  vendor  = data.pagerduty_vendor.cloudwatch.id
}

resource "pagerduty_service_integration" "cloudwatch_low_priority_notification" {
  name    = "Low Priority Notification for AWS Cloudwatch"
  service = pagerduty_service.mass_pfml_api_low_priority.id
  vendor  = data.pagerduty_vendor.cloudwatch.id
}
# Integration for Bandit and Safety
resource "pagerduty_service_integration" "security_scan_notification_channel" {
  name    = "Daily Security Scan for Bandit and Safety"
  service = pagerduty_service.mass_pfml_api_low_priority.id
  type    = "events_api_v2_inbound_integration"
}