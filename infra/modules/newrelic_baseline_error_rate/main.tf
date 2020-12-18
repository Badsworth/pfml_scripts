# Shared config for a New Relic NRQL Alert that triggers when the query returns a
# high percentage value. Used for a number of alert policies, so that
# we can identify when an endpoint begins to consistently fail.
resource "newrelic_nrql_alert_condition" "newrelic_baseline_error_rate" {
  # WARN: Query value above 90% for at least 5 minutes
  # CRITICAL: Query value equal to 100% for at least 5 minutes
  enabled   = true
  name      = var.name
  policy_id = var.policy_id

  # Collect data points for *10* minutes before running the function in the NRQL query.
  # A longer window can smooth out choppy data.
  aggregation_window = 600

  type                 = "static"
  value_function       = "single_value"
  violation_time_limit = "TWENTY_FOUR_HOURS"

  nrql {
    query             = var.query
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  warning {
    threshold_duration    = 300
    threshold             = 90
    operator              = "above"
    threshold_occurrences = "ALL"
  }

  critical {
    threshold_duration = 300
    # This is as high as it goes since 95% was still triggering false alarms for
    # the Employer Sign Up endpoint. We may want to further tune this for other
    # endpoints in the future, but this should hopefully cover worst case
    # scenario (endpoint being down entirely).
    threshold             = 100
    operator              = "equals"
    threshold_occurrences = "ALL"
  }
}
