# Shared config for a New Relic NRQL Alert that triggers when the query returns a
# high percentage value. Used for a number of alert policies, so that
# we can identify when an endpoint begins to consistently fail.
resource "newrelic_nrql_alert_condition" "newrelic_baseline_error_rate" {
  # WARN: Query value above 90% for at least 1 hour (4 aggregation windows)
  # CRITICAL: Query value equal to 100% for at least 1 hour (4 aggregation windows)
  enabled     = true
  name        = var.name
  policy_id   = var.policy_id
  runbook_url = "https://lwd.atlassian.net/l/c/6tXxK3DM"

  aggregation_window = 900 # max: 15 minutes

  # Fill empty aggregation windows with 0%
  fill_option = "static"
  fill_value  = 0

  type                         = "static"
  value_function               = "single_value"
  violation_time_limit_seconds = 86400 # 24 hours

  nrql {
    query             = var.query
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  warning {
    threshold_duration    = 3600
    threshold             = 90
    operator              = "above"
    threshold_occurrences = "ALL"
  }

  critical {
    threshold_duration = 3600
    # This is as high as it goes since 95% was still triggering false alarms for
    # the Employer Sign Up endpoint. We may want to further tune this for other
    # endpoints in the future, but this should hopefully cover worst case
    # scenario (endpoint being down entirely).
    threshold             = 100
    operator              = "equals"
    threshold_occurrences = "ALL"
  }
}

locals {
  app_name                     = "pfml-api"
  newrelic_account_id          = "2837112" # PFML's New Relic sub-account number
  newrelic_trusted_account_key = "1606654" # EOLWD's New Relic parent account number
}