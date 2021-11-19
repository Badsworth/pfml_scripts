locals {
  # List of endpoint groups that require alerts.
  # Each endpoint group will receive the following alarms:
  #
  # - Alarm for high 5XX error rate (excluding connectivity and timeout issues)
  # - Alarm for high 503/504 error rate (connectivity + timeout issues)
  # - Alarm for high 4XX error rate
  #
  endpoint_groups = {
    "notifications" = {
      alarm_name        = "High Notifications endpoint error rate"
      where_span_filter = "name LIKE 'POST paidleave-api%.mass.gov:80/api/v1/notifications'"
    }
    "service_now_api" = {
      alarm_name        = "High ServiceNow API error rate"
      where_span_filter = "name LIKE 'External/savilinx%.servicenowservices.com/requests/'"
    }
    "rmv_api" = {
      alarm_name        = "High RMV API error rate"
      where_span_filter = "name LIKE 'External/atlas-%'"
    }
    "fineos_api" = {
      alarm_name        = "High FINEOS API error rate"
      where_span_filter = "name LIKE 'External/%-api.masspfml.fineos.com/requests/'"
    }
  }
}

# Generate sets of alarms for each endpoint group; use the defaults for now.
module "endpoint_error_rates" {
  for_each = local.endpoint_groups
  source   = "../newrelic_endpoint_error_rates"

  alarm_name        = each.value.alarm_name
  environment_name  = var.environment_name
  where_span_filter = each.value.where_span_filter
  policy_id         = newrelic_alert_policy.api_alerts.id
}
