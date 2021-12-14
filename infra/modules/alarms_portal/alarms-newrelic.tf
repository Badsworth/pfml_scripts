# Terraform configuration for Browser alarms. (application-layer metrics, e.g. latency, error rate, traffic rate)

# ----------------------------------------------------------------------------------------------------------------------

resource "newrelic_alert_policy" "portal_alerts" {
  name                = "PFML Portal Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy" "low_priority_portal_alerts" {
  name                = "PFML Low Priority Portal Alerts (${upper(var.environment_name)})"
  account_id          = local.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

# This key was generated by Kevin Yeh on 10-21-2020 and should be replaced if he leaves.
# This was manually stored in SSM and is not managed through Terraform.
#
data "aws_ssm_parameter" "pagerduty_api_key" {
  name = "/admin/common/pagerduty-api-key"
}

locals {
  low_priority_channel_key  = var.low_priority_nr_portal_integration_key
  high_priority_channel_key = var.high_priority_nr_portal_integration_key

  alert_channel = {
    "test"        = local.low_priority_channel_key,
    "performance" = local.low_priority_channel_key,
    "training"    = local.low_priority_channel_key,
    "stage"       = local.low_priority_channel_key,
    "uat"         = local.low_priority_channel_key,
    "breakfix"    = local.low_priority_channel_key,
    "cps-preview" = local.low_priority_channel_key,
    "prod"        = local.high_priority_channel_key,
  }
}

resource "newrelic_alert_channel" "newrelic_portal_notifications" {
  name = "PFML Portal ${var.environment_name == "prod" ? "High" : "Low"} priority alerting channel"
  type = "pagerduty"

  config {
    service_key = local.alert_channel[var.environment_name]
  }
}

resource "newrelic_alert_policy_channel" "pfml_portal_alerts" {
  policy_id   = newrelic_alert_policy.portal_alerts.id
  channel_ids = [newrelic_alert_channel.newrelic_portal_notifications.id]
}

resource "newrelic_alert_channel" "newrelic_portal_prod_low_priority_notifications" {
  count = var.environment_name == "prod" ? 1 : 0
  name  = "PFML Portal Low priority alerting channel"
  type  = "pagerduty"

  config {
    service_key = local.low_priority_channel_key
  }
}

resource "newrelic_alert_policy_channel" "pfml_prod_low_priority_alerts" {
  count     = var.environment_name == "prod" ? 1 : 0
  policy_id = newrelic_alert_policy.low_priority_portal_alerts.id
  channel_ids = [
    newrelic_alert_channel.newrelic_portal_prod_low_priority_notifications[0].id
  ]
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
  # WARN: Average load time above 5 seconds for at least 5 minutes
  # CRIT: Average load time above 7 seconds for at least 10 minutes
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
    threshold     = 5 # units: seconds
  }

  term {
    priority      = "critical"
    time_function = "all" # e.g. "for at least..."
    duration      = 10    # units: minutes
    operator      = "above"
    threshold     = 7 # units: seconds
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

/////////////////////////
// NRQL Cognito Alerts //
/////////////////////////

locals {
  cognito_alerts = {
    "password_reset" = {
      name             = "High password reset error rate"
      interaction_name = "forgotPasswordSubmit"
    },
    "sign_in" = {
      name             = "High log in error rate"
      interaction_name = "signIn"
    }
    "claimant_sign_up" = {
      name             = "High claimant sign up error rate"
      interaction_name = "signUp"
      extra            = "AND groupedPageUrl NOT LIKE '%/employers/create-account'"
    }
    "claimant_sign_up_verification" = {
      name             = "High claimant sign up verification error rate"
      interaction_name = "confirmSignUp"
      extra            = "AND groupedPageUrl NOT LIKE '%/employers/create-account'"
    }
    "employer_sign_up" = {
      name             = "High employer sign up error rate"
      interaction_name = "signUp"
      extra            = "AND groupedPageUrl LIKE '%/employers/create-account'"
    }
  }
}

module "newrelic_alerts_cognito" {
  for_each = local.cognito_alerts

  source    = "../newrelic_baseline_error_rate"
  policy_id = newrelic_alert_policy.portal_alerts.id

  name  = each.value.name
  query = <<-NRQL
    SELECT percentage(count(*), WHERE httpResponseCode >= 400 AND httpResponseCode != 503 AND httpResponseCode != 504)
      * clamp_max(floor(uniqueCount(session) / 3), 1)
    FROM AjaxRequest
    WHERE browserInteractionName = 'fetch: cognito ${each.value.interaction_name}'
      AND hostname = 'cognito-idp.us-east-1.amazonaws.com'
      AND environment = '${var.environment_name}'
      ${lookup(each.value, "extra", "")}
  NRQL
}

//////////////////////////////////
// NRQL Application POST Alerts //
//////////////////////////////////

locals {
  application_post_errors = {
    "complete_application" = {
      name        = "High application completion error rate"
      request_url = "complete_application"
    }
    "document_upload" = {
      name        = "High document upload error rate"
      request_url = "documents"
    }
    "submit_application" = {
      name        = "High application submission error rate"
      request_url = "submit_application"
    }
    "submit_payment_preference" = {
      name        = "High payment preference submission error rate"
      request_url = "submit_payment_preference"
    }
  }
}

module "newrelic_alerts_application_post" {
  for_each = local.application_post_errors

  source    = "../newrelic_baseline_error_rate"
  policy_id = newrelic_alert_policy.portal_alerts.id

  name  = each.value.name
  query = <<-NRQL
    SELECT percentage(count(*), WHERE httpResponseCode >= 400 AND httpResponseCode != 503 AND httpResponseCode != 504)
      * clamp_max(floor(uniqueCount(user.auth_id) / 3), 1)
    FROM AjaxRequest
    WHERE httpMethod = 'POST'
      AND groupedRequestUrl LIKE '%/applications/*/${each.value.request_url}'
      AND environment = '${var.environment_name}'
  NRQL
}

locals {
  network_errors = {
    "cognito_api" = {
      name        = "High Cognito network error rate"
      request_url = "%cognito%"
    }
    "paid_leave_api" = {
      name        = "High API network error rate"
      request_url = "%paidleave%mass.gov%"
    }
  }
}

# Alarm for server-side network errors. The thresholds should be pretty high here
# since network issues are more unpredictable.
#
# Note that client-side network errors are not captured here. These are issues like:
# - cancelled (ajax request cancelled by the user)
# - failed to fetch (CORS issues or user navigated away from the page during a fetch)
#
resource "newrelic_nrql_alert_condition" "server_networkerror_surge" {
  for_each = local.network_errors

  # WARN: NetworkError percentage above 2% within the last 10 minutes, and at least 10 requests made per window
  # CRIT: NetworkError percentage above 5% within the last 10 minutes, and at least 10 requests made per window
  policy_id      = newrelic_alert_policy.portal_alerts.id
  type           = "static"
  value_function = "single_value"
  enabled        = true

  name = each.value.name
  nrql {
    query = <<-NRQL
      SELECT percentage(count(*), WHERE httpResponseCode = 503 OR httpResponseCode = 504)
        * clamp_max(floor(count(*) / 10), 1)
      FROM AjaxRequest
      WHERE environment = '${var.environment_name}'
        AND groupedRequestUrl LIKE '${each.value.request_url}'
    NRQL

    evaluation_offset = 1
  }

  violation_time_limit_seconds = 86400 # 24 hours
  aggregation_window           = 300   # calculate every 5 minutes e.g. TIMESERIES 5 MINUTES

  warning {
    # Warn if two 5-minute periods have error rate > 39% (at least 4/10 requests)
    threshold_duration    = 600
    threshold             = 39
    operator              = "above"
    threshold_occurrences = "ALL"
  }

  critical {
    # Set the alarm off if two 5-minute periods have error rate > 59% (at least 6/10 requests)
    threshold_duration    = 600
    threshold             = 59
    operator              = "above"
    threshold_occurrences = "ALL"
  }
}

locals {
  # Require at least 5 unique sessions per 15-minute window
  #
  # If there are fewer than 5 unique sessions, reset the detected error rate down to 0%
  # to prevent noisy false positives.
  #
  js_error_min_uniq_per_window = 5
  js_error_uniq_count          = "filter(uniqueCount(session), WHERE browserInteractionName NOT LIKE 'fetch:%')"
  js_error_total_count         = "filter(count(browserInteractionName), WHERE browserInteractionName NOT LIKE 'fetch:%')"
}

resource "newrelic_nrql_alert_condition" "javascripterror_surge" {
  # WARN: JavaScriptError percentage (errors/pageView) above 5% within the last 10 minutes, and at least 5 sessions active
  # CRIT: JavaScriptError percentage (errors/pageView) above 10% within the last 10 minutes, and at least 5 sessions active
  policy_id      = newrelic_alert_policy.portal_alerts.id
  name           = "JavaScriptErrors too high"
  type           = "static"
  value_function = "single_value"
  enabled        = true

  nrql {
    query = <<-NRQL
      SELECT (
        filter(
          count(errorMessage),
          WHERE errorMessage != 'undefined is not an object (evaluating \'ceCurrentVideo.currentTime\')'
            AND errorClass != 'NetworkError'
            AND errorMessage != 'Failed to fetch'
            AND errorMessage != 'cancelled'
            AND errorMessage != 'Network error'
            AND errorMessage NOT LIKE '%network connection%'
        ) / ${local.js_error_total_count}
      ) * clamp_max(floor(${local.js_error_uniq_count} / ${local.js_error_min_uniq_per_window}), 1)
      FROM JavaScriptError, BrowserInteraction
      WHERE appName = 'PFML-Portal-${upper(var.environment_name)}'
        AND pageUrl NOT LIKE '%localhost%'
        AND targetUrl NOT LIKE '%localhost%'
        AND errorMessage != 'Cannot set property \'status\' of undefined'
    NRQL

    evaluation_offset = 1
  }

  violation_time_limit_seconds = 86400 # 24 hours
  aggregation_window           = 300   # calculate every 5 minutes e.g. TIMESERIES 5 MINUTES

  warning {
    # Warn if two 5-minute periods have error rate > 5%
    threshold_duration    = 600
    threshold             = 0.05
    operator              = "above"
    threshold_occurrences = "ALL"
  }

  critical {
    # Set the alarm off if two 5-minute periods have error rate > 10%
    threshold_duration    = 600
    threshold             = 0.10
    operator              = "above"
    threshold_occurrences = "ALL"
  }
}


# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to errors in user account actions

module "cognito_sign_up_without_api_records" {
  # CRIT: API User records failed to create at least once
  source = "../newrelic_single_error_alarm"

  enabled     = true
  name        = "API records failed to create for new Cognito user"
  policy_id   = newrelic_alert_policy.low_priority_portal_alerts.id
  runbook_url = "https://lwd.atlassian.net/l/c/k9Uj81fH"

  nrql = <<-NRQL
    SELECT count(*) FROM Log
    WHERE aws.logGroup = 'service/pfml-api-${var.environment_name}'
      AND message LIKE 'API User records failed to save%'
  NRQL
}

module "cognito_sign_up_client_error" {
  # CRIT: Generic Cognito ClientError was raised at least once
  source = "../newrelic_single_error_alarm"

  enabled     = true
  name        = "Cognito sign up failed with unexpected ClientError"
  policy_id   = newrelic_alert_policy.low_priority_portal_alerts.id
  runbook_url = "https://lwd.atlassian.net/l/c/k9Uj81fH"

  nrql = <<-NRQL
    SELECT count(*) FROM Log
    WHERE aws.logGroup = 'service/pfml-api-${var.environment_name}'
      AND message = 'Failed to add user to Cognito due to unexpected ClientError'
  NRQL
}

module "portal_synthetic_ping_failure" {
  # Alarm on validation errors that should never happen, like type or enum mismatches.
  source = "../newrelic_single_error_alarm"

  # ignore performance and training environments
  enabled     = contains(["prod", "stage", "test"], var.environment_name)
  name        = "Portal synthetic ping failed"
  policy_id   = (var.environment_name == "prod") ? newrelic_alert_policy.low_priority_portal_alerts.id : newrelic_alert_policy.portal_alerts.id
  fill_option = "none"

  nrql = "SELECT filter(count(*), WHERE result = 'FAILED') FROM SyntheticCheck WHERE monitorName = 'portal_ping--${var.environment_name}'"
}

module "portal_scripted_synthetic_failure" {
  source = "../newrelic_single_error_alarm"

  # ignore performance and training environments
  enabled     = contains(["prod", "stage", "test"], var.environment_name)
  name        = "Portal usability check failed"
  description = "Checks if Portal is loading and not behind a maintenance page"
  policy_id   = (var.environment_name == "prod") ? newrelic_alert_policy.low_priority_portal_alerts.id : newrelic_alert_policy.portal_alerts.id
  fill_option = "none"

  nrql = "SELECT filter(count(*), WHERE result = 'FAILED') FROM SyntheticCheck WHERE monitorName = 'portal_scripted_synthetic--${var.environment_name}'"
}
