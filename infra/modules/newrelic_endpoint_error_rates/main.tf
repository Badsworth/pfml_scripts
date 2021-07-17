locals {
  # List of error groups to build alerts for.
  # For a given set of endpoints, we should have the following groups:
  #
  # - Fatal 5XX errors (excluding connectivity and timeout issues)
  # - 503/504 errors (temporary connectivity and timeout issues)
  # - 4XX errors
  #
  error_groups = {
    "5xx" = {
      error_group_name   = "5xx"
      status_code_filter = "(http.statusCode >= 500 AND http.statusCode != 503 AND http.statusCode != 504) OR (error.class IS NOT NULL AND error.class NOT IN ('requests.exceptions:%Timeout', 'requests.exceptions:ConnectionError'))"
    }
    "network" = {
      error_group_name   = "503/504"
      status_code_filter = "http.statusCode = 503 OR http.statusCode = 504"
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

  # WARN: % Error responses within the last 5 minutes exceed 10%
  # CRIT: % Error responses within the last 5 minutes exceed 33%
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
      ) * clamp_max(floor(count(*) / 5), 1) FROM Span
      WHERE ${var.where_span_filter}
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 1 # offset by the minimum of 1 window (5 minutes)
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold             = 10
    threshold_duration    = 300 # 5 minutes (1 window)
    operator              = "above"
    threshold_occurrences = "all"
  }

  critical {
    threshold             = 33
    threshold_duration    = 300 # 5 minutes (1 window)
    operator              = "above"
    threshold_occurrences = "all"
  }
}

