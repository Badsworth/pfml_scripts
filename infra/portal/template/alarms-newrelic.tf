# Terraform configuration for Browser alarms. (application-layer metrics, e.g. latency, error rate, traffic rate)

# ----------------------------------------------------------------------------------------------------------------------

resource "newrelic_alert_policy" "portal_alerts" {
  name                = "PFML Portal Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
  channel_ids         = []              # an eventual list of channels to inform // TODO: CP-418 - add channel IDs for PagerDuty chaannels.
}

resource "newrelic_alert_condition" "portal_ajax_response_time" {
  # WARN: Average response time above 3 seconds for at least 5 minutes
  # CRIT: Average response time above 5 seconds for at least 5 minutes
  policy_id       = newrelic_alert_policy.portal_alerts.id
  name            = "Portal AJAX response time too high"
  type            = "browser_metric"
  entities        = [data.newrelic_entity.pfml-portal.application_id]
  metric          = "ajax_response_time"
  condition_scope = "application"

  term {
    priority      = "warning"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 3 # units: seconds
  }

  term {
    priority      = "critical"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 5 # units: seconds
  }
}

resource "newrelic_alert_condition" "portal_page_load_time" {
  # WARN: Average load time above 2 seconds for at least 5 minutes
  # CRIT: Average load time above 5 seconds for at least 5 minutes
  policy_id       = newrelic_alert_policy.portal_alerts.id
  name            = "Portal page load time too high"
  type            = "browser_metric"
  entities        = [data.newrelic_entity.pfml-portal.application_id]
  metric          = "total_page_load"
  condition_scope = "application"

  term {
    priority      = "warning"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 3 # units: seconds
  }

  term {
    priority      = "critical"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 5 # units: seconds
  }
}

resource "newrelic_alert_condition" "portal_page_rendering_time" {
  # WARN: Average rendering time above 2 seconds for at least 5 minutes
  # CRIT: Average rendering time above 3 seconds for at least 5 minutes
  policy_id       = newrelic_alert_policy.portal_alerts.id
  name            = "Portal page rendering time too high"
  type            = "browser_metric"
  entities        = [data.newrelic_entity.pfml-portal.application_id]
  metric          = "page_rendering"
  condition_scope = "application"

  term {
    priority      = "warning"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 2 # units: seconds
  }

  term {
    priority      = "critical"
    time_function = "all" # e.g. "for at least..."
    duration      = 5     # units: minutes
    operator      = "above"
    threshold     = 3 # units: seconds
  }
}

/////////////////
// NRQL Alerts //
/////////////////

resource "newrelic_nrql_alert_condition" "javascripterror_surge" {
  # WARN: JavaScriptError percentage (errors/pageView) above 2% for at least 5 minutes
  # CRIT: JavaScriptError percentage (errors/pageView) above 5% for at least 5 minutes
  policy_id      = newrelic_alert_policy.portal_alerts.id
  name           = "JavaScriptErrors too high"
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = "SELECT count(errorMessage) / count(pageUrl) from JavaScriptError, PageView WHERE appName = 'PFML-Portal-${upper(var.environment_name)}'"
    evaluation_offset = 1
  }

  violation_time_limit = "TWENTY_FOUR_HOURS"

  warning {
    threshold_duration    = 300
    threshold             = 0.02
    operator              = "above"
    threshold_occurrences = "ALL"
  }

  critical {
    threshold_duration    = 300
    threshold             = 0.05
    operator              = "above"
    threshold_occurrences = "ALL"
  }
}
