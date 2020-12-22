# Terraform configuration for APM alarms. (application-layer metrics, e.g. latency, error rate, traffic rate)

# ----------------------------------------------------------------------------------------------------------------------

resource "newrelic_alert_policy" "api_alerts" {
  name                = "PFML API Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
  channel_ids         = []              # an eventual list of channels to inform
}

# This key was generated by Kevin Yeh on 10-21-2020 and should be replaced if he leaves.
# This was manually stored in SSM and is not managed through Terraform.
# 
data "aws_ssm_parameter" "pagerduty_api_key" {
  name = "/admin/common/pagerduty-api-key"
}

locals {
  low_priority_channel_key  = data.terraform_remote_state.pagerduty.outputs.low_priority_nr_integration_key
  high_priority_channel_key = data.terraform_remote_state.pagerduty.outputs.high_priority_nr_integration_key

  alert_channel = {
    "test"        = local.low_priority_channel_key,
    "performance" = local.low_priority_channel_key,
    "training"    = local.low_priority_channel_key,
    "stage"       = local.low_priority_channel_key,
    "prod"        = local.high_priority_channel_key,
  }
}
resource "newrelic_alert_channel" "newrelic_api_notifications" {
  name = "PFML API ${var.environment_name == "prod" ? "High" : "Low"} priority alerting channel"
  type = "pagerduty"

  config {
    service_key = local.alert_channel[var.environment_name]
  }
}

resource "newrelic_alert_policy_channel" "pfml_alerts" {
  policy_id   = newrelic_alert_policy.api_alerts.id
  channel_ids = [newrelic_alert_channel.newrelic_api_notifications.id]
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
  # CRIT: traffic below 100 rpm (well below the "no one is using the app" traffic baseline) for at least five minutes
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
    threshold     = 100 # units: requests per minute
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

////////////////
// RDS Alerts //
////////////////

resource "newrelic_nrql_alert_condition" "rds_high_cpu_utilization" {
  # WARN: CPU Utilization above 75% for at least 5 minutes
  # CRIT: CPU Utilization above 90% for at least 5 minutes
  policy_id      = newrelic_alert_policy.api_alerts.id
  name           = "RDS CPU Utilization too high"
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = "SELECT percentile(`provider.cpuUtilization.total`, 99) from DatastoreSample where provider = 'RdsDbInstance' and displayName = '${aws_db_instance.default.identifier}'"
    evaluation_offset = 3
  }

  violation_time_limit = "TWENTY_FOUR_HOURS"

  warning {
    threshold_duration    = 300
    threshold             = 75
    operator              = "above"
    threshold_occurrences = "ALL"
  }

  critical {
    threshold_duration    = 300
    threshold             = 90
    operator              = "above"
    threshold_occurrences = "ALL"
  }
}

resource "newrelic_nrql_alert_condition" "rds_low_storage_space" {
  # WARN: RDS storage space is below 30% for at least 5 minutes
  # CRIT: RDS storage space is below 20% for at least 5 minutes
  policy_id      = newrelic_alert_policy.api_alerts.id
  name           = "RDS instance has <= 20% free storage space"
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = "SELECT average(provider.freeStorageSpaceBytes.Maximum) / average(provider.allocatedStorageBytes ) * 100 FROM DatastoreSample where provider = 'RdsDbInstance' and displayName = '${aws_db_instance.default.identifier}'"
    evaluation_offset = 3
  }

  violation_time_limit = "TWENTY_FOUR_HOURS"

  warning {
    threshold_duration    = 300
    threshold             = 30
    operator              = "below"
    threshold_occurrences = "ALL"
  }

  critical {
    threshold_duration    = 300
    threshold             = 20
    operator              = "below"
    threshold_occurrences = "ALL"
  }
}

///////////////////
// FINEOS Alerts //
///////////////////

resource "newrelic_nrql_alert_condition" "fineos_error_rate_5XXs" {
  # WARN: % FINEOS responses that are 5XXs exceed 10% for 5 minutes
  # CRIT: % FINEOS responses that are 5XXs exceed 15% for 2 minutes
  name           = "FINEOS 5XXs response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = "SELECT percentage(COUNT(*), WHERE http.statusCode >= 500) FROM Span WHERE name LIKE 'External/%-api.masspfml.fineos.com/requests/' AND appName = 'PFML-API-${upper(var.environment_name)}'"
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit = "TWENTY_FOUR_HOURS"

  warning {
    threshold_duration    = 300
    threshold             = 10
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 120
    threshold             = 15
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }
}

resource "newrelic_nrql_alert_condition" "fineos_error_rate_4XXs" {
  # WARN: % FINEOS responses that are 4XXs exceed 10% for 5 minutes
  # CRIT: % FINEOS responses that are 4XXs exceed 15% for 2 minutes
  name           = "FINEOS 4XXs response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = "SELECT percentage(COUNT(*), WHERE http.statusCode >= 400 and http.statusCode < 500) FROM Span WHERE name LIKE 'External/%-api.masspfml.fineos.com/requests/' AND appName = 'PFML-API-${upper(var.environment_name)}'"
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit = "TWENTY_FOUR_HOURS"

  warning {
    threshold             = 10
    threshold_duration    = 300
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold             = 15
    threshold_duration    = 120
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }
}
