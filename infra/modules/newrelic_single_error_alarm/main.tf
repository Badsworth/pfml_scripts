# Aggregation Window: 1 minute
# Threshold Duration: 5 windows (5 minutes)
# Evaluation Offset: 2 windows (2 minutes)
#
# Query: TIMESERIES 1 MINUTE SINCE 7 MINUTES AGO UNTIL 2 MINUTES AGO
# - Triggers 2 minutes after a violation
#
# Default fill_option:
# - Resolves 7 minutes after the last non-violating datapoint
#
# fill_option = 'none':
# - Resolves 7 minutes after the last *violating* datapoint
#
locals {
  alert_window_seconds = 60 # 1 minute
}

resource "newrelic_nrql_alert_condition" "alert" {
  name           = var.name
  description    = var.description
  type           = "static"
  value_function = "single_value"
  enabled        = var.enabled
  policy_id      = var.policy_id
  runbook_url    = var.runbook_url

  # Fill empty windows with the last value by default
  # so any alarm violations will stay open up until
  # the violation time limit.
  #
  # If you have a more frequent dataset (e.g. synthetic that runs every 5 minutes),
  # you should optimize for a faster-resolving alarm and set this to 'none'.
  #
  fill_option                  = var.fill_option
  aggregation_window           = local.alert_window_seconds
  violation_time_limit_seconds = 86400

  nrql {
    evaluation_offset = 2
    query             = var.nrql
  }

  critical {
    threshold             = 0
    threshold_duration    = local.alert_window_seconds * 5
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }
}
