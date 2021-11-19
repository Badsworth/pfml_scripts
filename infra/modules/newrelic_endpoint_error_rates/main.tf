#
# New Relic alert conditions for endpoint calls.
#
# This can be used for incoming calls or outgoing calls (other APIs) depending on the where_span_filter.
#

locals {
  # List of error groups to build alerts for.
  # For a given set of endpoints, we should have the following groups:
  #
  # - 5XX errors and errors where we didn't get a response code (failed connections, timeout, etc.)
  # - 4XX errors
  #
  error_groups = {
    "5xx" = {
      error_group_name   = "5xx"
      status_code_filter = "http.statusCode >= 500 OR error.class IS NOT NULL"
    }
    "4xx" = {
      error_group_name   = "4xx"
      status_code_filter = "http.statusCode >= 400 AND http.statusCode < 500"
    }
  }
}

# For each error group, create a rate-based alert.
resource "newrelic_nrql_alert_condition" "endpoint_error_rates" {
  for_each = local.error_groups

  name           = "[${each.value.error_group_name}] ${var.alarm_name}"
  policy_id      = var.policy_id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  aggregation_window = 300 # calculate every 5 minutes

  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE ${each.value.status_code_filter}
      ) FROM Span
      WHERE ${var.where_span_filter}
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 1 # offset by the minimum of 1 window (5 minutes)
  }

  violation_time_limit_seconds = 86400 # 24 hours

  # Look for "slow burn" problems - a low but persistent rate of errors.
  warning {
    threshold             = 5
    threshold_duration    = 1800 # 30 minutes
    operator              = "above"
    threshold_occurrences = "all"
  }

  # Sudden serious problems - most calls start failing.
  critical {
    threshold             = 80
    threshold_duration    = 300 # 5 minutes (1 window)
    operator              = "above"
    threshold_occurrences = "all"
  }
}
