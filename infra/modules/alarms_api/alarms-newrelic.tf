# Terraform configuration for any alarm that's stored in New Relic.

# ----------------------------------------------------------------------------------------------------------------------
# High-level administrative objects: (empty) alert policies, notification channels, etc.

resource "newrelic_alert_policy" "api_alerts" {
  name                = "PFML API Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy" "low_priority_api_alerts" {
  name                = "PFML Low Priority API Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

# This key was generated by Kevin Yeh on 10-21-2020 and should be replaced if he leaves.
# This was manually stored in SSM and is not managed through Terraform.
##
data "aws_ssm_parameter" "pagerduty_api_key" {
  name = "/admin/common/pagerduty-api-key"
}

locals {
  low_priority_channel_key  = var.low_priority_nr_integration_key
  high_priority_channel_key = var.high_priority_nr_integration_key

  alert_channel = {
    "test"        = local.low_priority_channel_key,
    "performance" = local.low_priority_channel_key,
    "training"    = local.low_priority_channel_key,
    "stage"       = local.low_priority_channel_key,
    "uat"         = local.low_priority_channel_key,
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
  policy_id = newrelic_alert_policy.api_alerts.id
  channel_ids = [
    newrelic_alert_channel.newrelic_api_notifications.id
  ]
}

resource "newrelic_alert_channel" "newrelic_api_prod_low_priority_notifications" {
  count = var.environment_name == "prod" ? 1 : 0
  name  = "PFML API Low priority alerting channel"
  type  = "pagerduty"

  config {
    service_key = local.low_priority_channel_key
  }
}

resource "newrelic_alert_policy_channel" "pfml_prod_low_priority_alerts" {
  count     = var.environment_name == "prod" ? 1 : 0
  policy_id = newrelic_alert_policy.low_priority_api_alerts.id
  channel_ids = [
    newrelic_alert_channel.newrelic_api_prod_low_priority_notifications[0].id
  ]
}

# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to the API's generic performance metrics

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

# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to the API's RDS database

resource "newrelic_nrql_alert_condition" "rds_high_cpu_utilization" {
  # WARN: CPU Utilization above 75% for at least 5 minutes
  # CRIT: CPU Utilization above 90% for at least 5 minutes
  policy_id      = newrelic_alert_policy.api_alerts.id
  name           = "RDS CPU Utilization too high"
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = "SELECT percentile(`provider.cpuUtilization.total`, 99) from DatastoreSample where provider = 'RdsDbInstance' and displayName = data.aws_db_instance.default.db_instance_identifier"
    evaluation_offset = 3
  }

  violation_time_limit_seconds = 86400 # 24 hours

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
    query             = "SELECT average(provider.freeStorageSpaceBytes.Maximum) / average(provider.allocatedStorageBytes ) * 100 FROM DatastoreSample where provider = 'RdsDbInstance' and displayName = data.aws_db_instance.default.db_instance_identifier"
    evaluation_offset = 3
  }

  violation_time_limit_seconds = 86400 # 24 hours

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

# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to errors from FINEOS

resource "newrelic_nrql_alert_condition" "fineos_aggregated_5xx_rate" {
  # WARN: FINEOS responses that are 5XXs exceed 10% at least once in the last 5 minutes
  # CRIT: FINEOS responses that are 5XXs exceed 33% for all of the last 5 minutes
  name           = "FINEOS 5XXs response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE name LIKE 'External/%-api.masspfml.fineos.com/requests/'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold_duration    = 300 # five minutes
    threshold             = 10  # units: percentage
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 300 # five minutes
    threshold             = 33  # units: percentage
    operator              = "above"
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "fineos_aggregated_4xx_rate" {
  # WARN: % FINEOS responses that are 4XXs exceed 10% for 5 minutes
  # CRIT: % FINEOS responses that are 4XXs exceed 33% for 5 minutes
  name           = "FINEOS 4XXs response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 400 and http.statusCode < 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE name LIKE 'External/%-api.masspfml.fineos.com/requests/'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold             = 10
    threshold_duration    = 300 # 5 minutes
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold             = 33
    threshold_duration    = 300 # 5 minutes
    operator              = "above"
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "fineos_claim-submission_5xx_rate" {
  # CONDITION: Percentage of 5xx responses from all FINEOS endpoints used by the API's 'submit_application' endpoint
  # CRIT: This percentage is > 33% for at least 5 minutes
  # WARN: This percentage is > 10% for any 1 minute in a 5 minute window

  name                         = "[5xx] High rate of claim submission failure in ${upper(var.environment_name)} FINEOS"
  policy_id                    = newrelic_alert_policy.api_alerts.id
  type                         = "static"
  value_function               = "single_value"
  enabled                      = true
  violation_time_limit_seconds = 86400 # 24 hours

  nrql {
    query = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE http.url LIKE 'https://%-api.masspfml.fineos.com/integration-services/wscomposer/ReadEmployer'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/integration-services/wscomposer/webservice'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/updateCustomerDetails'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/absence/startAbsence'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/updateCustomerContactDetails'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/absence/%/reflexive-questions'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/cases/%/occupations'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/occupations/%/week-based-work-pattern%'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/absence/notifications/%/complete-intake'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL

    evaluation_offset = 3
  }

  warning {
    threshold_duration    = 300 # five minutes
    threshold             = 10  # units: percentage
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 300 # five minutes
    threshold             = 33  # units: percentage
    operator              = "above"
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "fineos_claim-submission_4xx_rate" {
  # CONDITION: Percentage of 4xx responses from all FINEOS endpoints used by the API's 'submit_application' endpoint
  # CRIT: This percentage is > 33% for at least 5 minutes
  # WARN: This percentage is > 10% for any 1 minute in a 5 minute window

  name                         = "[4xx] High rate of claim submission failure in ${upper(var.environment_name)} FINEOS"
  policy_id                    = newrelic_alert_policy.api_alerts.id
  type                         = "static"
  value_function               = "single_value"
  enabled                      = true
  violation_time_limit_seconds = 86400 # 24 hours

  nrql {
    query = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 400 and http.statusCode < 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE http.url LIKE 'https://%-api.masspfml.fineos.com/integration-services/wscomposer/ReadEmployer'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/integration-services/wscomposer/webservice'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/updateCustomerDetails'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/absence/startAbsence'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/updateCustomerContactDetails'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/absence/%/reflexive-questions'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/cases/%/occupations'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/occupations/%/week-based-work-pattern%'
        OR http.url LIKE 'https://%-api.masspfml.fineos.com/customerapi/customer/absence/notifications/%/complete-intake'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL

    evaluation_offset = 3
  }

  warning {
    threshold_duration    = 300 # five minutes
    threshold             = 10  # units: percentage
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 300 # five minutes
    threshold             = 33  # units: percentage
    operator              = "above"
    threshold_occurrences = "all"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to errors in the /notifications endpoint where FINEOS POSTs new claims

resource "newrelic_nrql_alert_condition" "notifications_endpoint_error_rate" {
  # WARN: % Error responses exceed 10% at least once in 5 minutes
  # CRIT: % Error responses exceed 33% for a continuous 5 minute window
  name           = "Notifications endpoint error rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE response.statusCode >= 400 OR error.class IS NOT NULL
      ) FROM Span
      WHERE name LIKE 'POST paidleave-api-%.mass.gov:80/api/v1/notifications'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold             = 10
    threshold_duration    = 300 # 5 minutes
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold             = 33
    threshold_duration    = 300 # 5 minutes
    operator              = "above"
    threshold_occurrences = "all"
  }
}


# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to errors from ServiceNow

resource "newrelic_nrql_alert_condition" "servicenow_4xx_rate" {
  # WARN: ServiceNow responses that are 4XXs exceed 10% at least once in the last 5 minutes
  # CRIT: ServiceNow responses that are 4XXs exceed 33% for all of the last 5 minutes
  name           = "ServiceNow error response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 400 AND http.statusCode < 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE name LIKE 'External/savilinx.servicenowservices.com/requests/'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold_duration    = 300 # five minutes
    threshold             = 10  # units: percentage
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 300 # five minutes
    threshold             = 33  # units: percentage
    operator              = "above"
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "servicenow_5xx_rate" {
  # WARN: ServiceNow responses that are 5XXs exceed 10% at least once in the last 5 minutes
  # CRIT: ServiceNow responses that are 5XXs exceed 33% for all of the last 5 minutes
  name           = "ServiceNow error response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE name LIKE 'External/savilinx.servicenowservices.com/requests/'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold_duration    = 300 # five minutes
    threshold             = 10  # units: percentage
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 300 # five minutes
    threshold             = 33  # units: percentage
    operator              = "above"
    threshold_occurrences = "all"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# Alarms relating to problems in the payments pipeline

resource "newrelic_nrql_alert_condition" "payments_errors_from_fineos" {
  count                        = (var.environment_name == "prod") ? 1 : 0
  name                         = "Errors encountered by the payments-fineos-process task"
  type                         = "static"
  value_function               = "single_value"
  enabled                      = true
  policy_id                    = (var.environment_name == "prod") ? newrelic_alert_policy.low_priority_api_alerts.id : newrelic_alert_policy.api_alerts.id
  violation_time_limit_seconds = 86400 # 24 hours

  nrql {
    evaluation_offset = 3
    query             = <<-NRQL
      SELECT count(*) FROM Log
      WHERE aws.logGroup = 'service/pfml-api-prod/ecs-tasks'
      AND aws.logStream LIKE 'prod/payments-fineos-process/%'
      AND levelname = 'ERROR'
    NRQL
  }

  critical {
    threshold             = 0
    threshold_duration    = 120
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }
}

resource "newrelic_nrql_alert_condition" "payments_errors_from_comptroller" {
  count                        = (var.environment_name == "prod") ? 1 : 0
  name                         = "Errors encountered by the payments-ctr-process task"
  type                         = "static"
  value_function               = "single_value"
  enabled                      = true
  policy_id                    = (var.environment_name == "prod") ? newrelic_alert_policy.low_priority_api_alerts.id : newrelic_alert_policy.api_alerts.id
  violation_time_limit_seconds = 86400 # 24 hours

  nrql {
    evaluation_offset = 3
    query             = <<-NRQL
      SELECT count(*) FROM Log
      WHERE aws.logGroup = 'service/pfml-api-prod/ecs-tasks'
      AND aws.logStream LIKE 'prod/payments-ctr-process/%'
      AND levelname = 'ERROR'
    NRQL
  }

  critical {
    threshold             = 0
    threshold_duration    = 120
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# Alarms relating to RMV 5xxs

resource "newrelic_nrql_alert_condition" "rmv_5xx_rate" {
  # WARN: RMV responses that are 5XXs exceed 10% at least once in the last 5 minutes
  # CRIT: RMV responses that are 5XXs exceed 33% for all of the last 5 minutes
  name           = "RMV error response rate too high"
  policy_id      = newrelic_alert_policy.api_alerts.id
  type           = "static"
  value_function = "single_value"
  fill_option    = "last_value"
  enabled        = true

  # the extra error.class filter is here to catch SSL or timeout errors that do not possess an HTTP status code
  nrql {
    query             = <<-NRQL
      SELECT percentage(
        COUNT(*), WHERE http.statusCode >= 500 OR error.class IS NOT NULL
      ) FROM Span
      WHERE name LIKE 'External/atlas-%'
      AND appName = 'PFML-API-${upper(var.environment_name)}'
    NRQL
    evaluation_offset = 3 # recommended offset from the Terraform docs for this resource
  }

  violation_time_limit_seconds = 86400 # 24 hours

  warning {
    threshold_duration    = 300 # five minutes
    threshold             = 10  # units: percentage
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 300 # five minutes
    threshold             = 33  # units: percentage
    operator              = "above"
    threshold_occurrences = "all"
  }
}
