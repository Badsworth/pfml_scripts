resource "newrelic_alert_policy" "sns_alerts" {
  name                = "PFML AWS Account Alerts for SNS"
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy" "low_priority_sns_alerts" {
  name                = "PFML AWS Account Low Priority Alerts for SNS"
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy" "service_desk_alerts" {
  name                = "PFML AWS Account SNS Service Desk Alerts"
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_channel" "newrelic_sns_notifications" {
  name = "PFML AWS Account Alerts channel"
  type = "pagerduty"
}

resource "newrelic_alert_policy_channel" "pfml_sns_alerts" {
  policy_id = newrelic_alert_policy.sns_alerts.id
  channel_ids = [
    newrelic_alert_channel.newrelic_sns_notifications.id
  ]
}

# ------------------------------------------------------------------------------------------------

# This email goes to the service desk and to API on-call engineers.
# If you are on-call, you receive this for visibility and do not need to take action at this time.
# The service desk will reach out as needed with any questions.

resource "newrelic_alert_channel" "newrelic_service_desk_notifications" {
  name = "PFML API Service Desk alerting channel"
  type = "email"

  config {
    recipients              = "EOL-DL-DFML-PFML-SERVICE-DESK@mass.gov, mass-pfml-api-low-priority@navapbc.pagerduty.com"
    include_json_attachment = "true"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# Alerts relating to SNS Spending Limits and Errors

resource "newrelic_nrql_alert_condition" "sns_spending_limit" {
  # CRIT: sns spendlng greater than limit.

  name               = "sns-spending-limit"
  policy_id          = newrelic_alert_policy.sns_alerts.id
  type               = "static"
  value_function     = "single_value"
  enabled            = true
  aggregation_window = local.default_aggregation_period # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    #
    query = <<-NRQL
      SELECT count(delivery.providerResponse LIKE 'This delivery would exceed max price') FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  critical {
    threshold_duration    = local.default_aggregation_period # period in aws_cloudwatch_metric_alarm
    threshold             = 1                                # threshold in aws_cloudwatch_metric_alarm
    operator              = "above"                          # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "sns_failure_rate" {
  # WARN: SMS failure rate to phone numbers is 25% for 1 hour
  # CRIT: SMS failure rate to phone numbers is 50% for 1 hour.

  name               = "sns-sms-failure-rate"
  policy_id          = newrelic_alert_policy.sns_alerts.id
  type               = "static"
  value_function     = "single_value"
  enabled            = true
  aggregation_window = local.default_aggregation_period #

  nrql {
    query = <<-NRQL
      SELECT count(provider.numberOfNotificationsFailed.Sum)/count(provider.numberOfMessagesPublished.Sum) FROM QueueSample SINCE 1 hour AGO TIMESERIES
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds
  warning {
    threshold_duration    = 60
    threshold             = 0.25
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 60
    threshold             = 0.5
    operator              = "above"
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_phone_carrier_unavailable" {
  # WARN: More than 10 SMS failed because a phone carrier is unavailable over 1 hours.
  # CRIT: More than 10 SMS failed because a phone carrier is unavailable over 2 hours.

  name               = "sns-spending-limit"
  policy_id          = newrelic_alert_policy.sns_alerts.id
  type               = "static"
  value_function     = "single_value"
  enabled            = true
  aggregation_window = 7200 # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    #
    query = <<-NRQL
      SELECT count(delivery.providerResponse LIKE 'Phone carrier is currently unreachable/unavailable') FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  # statistic is sum in this case
  warning {
    threshold_duration    = 3600    # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 10      # threshold in aws_cloudwatch_metric_alarm
    operator              = "above" # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = 7200    # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 10      # threshold in aws_cloudwatch_metric_alarm
    operator              = "above" # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_blocked_as_spam" {
  # More than 10 SMS have been blocked as spam over 2 hours.

  name               = "sns_sms_blocked_as_spam"
  policy_id          = newrelic_alert_policy.sns_alerts.id
  type               = "static"
  value_function     = "single_value"
  enabled            = true
  aggregation_window = 60 * 6 # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {

    query = <<-NRQL
      SELECT count(delivery.providerResponse LIKE 'Blocked as spam by phone carrier') FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds
  // statistic is sum in this case

  critical {
    threshold_duration    = 7200    # period in aws_cloudwatch_metric_alarm
    threshold             = 10      # threshold in aws_cloudwatch_metric_alarm
    operator              = "above" # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "all"
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_rate_exceeded" {
  # At least 1 SNS SMS rate exceeded error in 5 minutes

  name               = "sns-spending-limit"
  policy_id          = newrelic_alert_policy.sns_alerts.id
  type               = "static"
  value_function     = "single_value"
  enabled            = true
  aggregation_window = local.default_aggregation_period # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    query = <<-NRQL
      SELECT count(delivery.providerResponse LIKE 'Rate exceeded') FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  # statistic is sum in this case

  critical {
    threshold_duration    = local.default_aggregation_period # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 1                                # threshold in aws_cloudwatch_metric_alarm
    operator              = "above"                          # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "all"
  }
}
