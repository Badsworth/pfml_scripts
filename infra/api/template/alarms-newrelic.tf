# Terraform configuration for APM alarms. (application-layer metrics, e.g. latency, error rate, traffic rate)

# ----------------------------------------------------------------------------------------------------------------------

resource "newrelic_alert_policy" "api_alerts" {
  name                = "PFML API Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
  channel_ids         = []              # an eventual list of channels to inform
}

resource "newrelic_alert_condition" "api_error_rate" {
  # WARN: error rate above 1% for at least five minutes
  # CRIT: error rate above 10% at least once in any five-minute period
  policy_id       = newrelic_alert_policy.api_alerts.id
  name            = "API error rate too high"
  type            = "apm_app_metric"
  entities        = [data.newrelic_entity.pfml-api.application_id]
  metric          = "error_percentage"
  condition_scope = "application"

  term {
    priority      = "warning"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 1 # units: percentage
  }

  term {
    priority      = "critical"
    time_function = "any" # e.g. "at least once in..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 10 # units: percentage
  }
}

resource "newrelic_alert_condition" "api_traffic_rate" {
  # CRIT: traffic below 200 rpm (the approx. "no one is using the app" traffic baseline) for at least five minutes
  policy_id       = newrelic_alert_policy.api_alerts.id
  name            = "API traffic below normal baseline"
  type            = "apm_app_metric"
  entities        = [data.newrelic_entity.pfml-api.application_id]
  metric          = "throughput_web"
  condition_scope = "application"

  term {
    priority      = "critical"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "below"
    threshold     = 200 # units: requests per minute
  }
}

resource "newrelic_alert_condition" "api_response_time" {
  # WARN: Average response time above 250ms for at least ten minutes
  # CRIT: Average response time above 2½sec for at least ten minutes
  policy_id       = newrelic_alert_policy.api_alerts.id
  name            = "API response time too high"
  type            = "apm_app_metric"
  entities        = [data.newrelic_entity.pfml-api.application_id]
  metric          = "response_time_web"
  condition_scope = "application"

  term {
    priority      = "warning"
    time_function = "all" # e.g. "for at least..."
    duration      = 10    # units: minutes
    operator      = "above"
    threshold     = 0.25 # units: seconds
  }

  term {
    priority      = "critical"
    time_function = "all" # e.g. "for at least..."
    duration      = 10    # units: minutes
    operator      = "above"
    threshold     = 2.5 # units: seconds
  }
}
