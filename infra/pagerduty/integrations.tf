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

