resource "newrelic_nrql_alert_condition" "sns_spending_limit" {
  # CRIT: sns spendlng greater than limit.

  name               = "sns-spending-limit"
  policy_id          = newrelic_alert_policy.sns_alerts.id
  type               = "static"
  value_function     = "single_value"
  enabled            = true
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    #
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}' WHERE delivery.providerResponse = 'This delivery would exceed max price'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  critical {
    threshold_duration    = local.default_aggregation_window # period in aws_cloudwatch_metric_alarm
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
  aggregation_window = local.default_aggregation_window #

  nrql {
    query = <<-NRQL
      SELECT count(provider.numberOfNotificationsFailed.Sum)/count(provider.numberOfMessagesPublished.Sum) FROM QueueSample
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds
  warning {
    threshold_duration    = local.one_hour
    threshold             = 0.6
    operator              = "above"
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = local.one_hour
    threshold             = 0.75 # current average rate is 0.5
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
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    #
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}' WHERE delivery.providerResponse = 'Phone carrier is currently unreachable/unavailable'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  # statistic is sum in this case
  warning {
    threshold_duration    = local.one_hour
    threshold             = 10      # threshold in aws_cloudwatch_metric_alarm
    operator              = "above" # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = local.one_hour * 2
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
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {

    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}' WHERE delivery.providerResponse = 'Blocked as spam by phone carrier'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  critical {
    threshold_duration    = local.one_hour * 2 # period in aws_cloudwatch_metric_alarm
    threshold             = 10                 # threshold in aws_cloudwatch_metric_alarm
    operator              = "above"            # comparison_operator in aws_cloudwatch_metric_alarm
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
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_failure_log_group_name}' WHERE delivery.providerResponse = 'Rate exceeded'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  # statistic is sum in this case

  critical {
    threshold_duration    = local.default_aggregation_window # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 1                                # threshold in aws_cloudwatch_metric_alarm
    operator              = "above"                          # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "all"
  }
}
