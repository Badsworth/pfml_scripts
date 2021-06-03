locals {
  pagerduty_services = {
    "api_low"     = pagerduty_service.mass_pfml_api_low_priority.id,
    "api_high"    = pagerduty_service.mass_pfml_api_high_priority.id,
    "portal_low"  = pagerduty_service.mass_pfml_portal_low_priority.id,
    "portal_high" = pagerduty_service.mass_pfml_portal_high_priority.id,
  }
}

# This service event rule renames alerts of the form:
#
#   PFML Low Priority API Alerts (PROD) (Log query violated Errors encountered by the payments-fineos-process task)
#
# and removes the boilerplate:
#
#   (API PROD) Errors encountered by the payments-fineos-process task
#
# This resource works by defining three blocks:
# - conditions: determines which alerts it runs on
# - variables: captures different variables from existing alert fields, based on regexes
# - actions: renames the alert title using the variables
#
resource "pagerduty_service_event_rule" "rename_query_violations" {
  for_each = locals.pagerduty_services
  service  = each.value
  disabled = "false"

  # When the alert title matches this regex...
  conditions {
    operator = "contains"
    parameter {
      value = "PFML.*Alerts.*query violated"
      path  = "summary"
    }
  }

  # Capture the alarm_description from the "component" field
  variable {
    type = "regex"
    name = "alarm_description"
    parameters {
      value = "(.*)"
      path  = "component"
    }
  }

  # Capture the environment name from the alert title
  variable {
    type = "regex"
    name = "environment"
    parameters {
      value = "PFML.*Alerts \\(([a-zA-Z]*)\\) \\(.*\\)"
      path  = "summary"
    }
  }

  # Capture the service (API or Portal) from the alert title
  variable {
    type = "regex"
    name = "service"
    parameters {
      value = "PFML.* ([a-zA-Z]*) Alerts .*"
      path  = "summary"
    }
  }

  # With all of the captured variables, set the new alert title
  actions {
    extractions {
      target   = "summary"
      template = "({{service}} {{environment}}) {{alarm_description}}"
    }
  }
}
