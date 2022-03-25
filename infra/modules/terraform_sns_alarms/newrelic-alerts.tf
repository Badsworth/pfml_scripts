resource "newrelic_nrql_alert_condition" "sns_spending_limit" {
  # CRIT: sns spendlng greater than limit.

  name               = "${local.prefix}sns-spending-limit"
  policy_id          = newrelic_alert_policy.pfml_aws_sns_high_priority_alert.id
  type               = local.condition_type
  value_function     = local.value_function
  enabled            = true
  aggregation_delay  = local.aggregation_delay
  aggregation_method = local.aggregation_method
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    #
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_log_group_name}' WHERE delivery.providerResponse = 'This delivery would exceed max price'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  critical {
    threshold_duration    = local.default_aggregation_window   # period in aws_cloudwatch_metric_alarm
    threshold             = 1                                  # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = local.threshold_occurrences
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_failure_rate" {
  # WARN: SMS failure rate to phone numbers is 60% for 2 hours
  # CRIT: SMS failure rate to phone numbers is 75% for 2 hours

  name               = "${local.prefix}sns-sms-failure-rate"
  policy_id          = newrelic_alert_policy.pfml_aws_sns_high_priority_alert.id
  type               = local.condition_type
  value_function     = local.value_function
  enabled            = true
  aggregation_delay  = local.aggregation_delay
  aggregation_method = local.aggregation_method
  aggregation_window = local.default_aggregation_window #

  nrql {
    query = <<-NRQL
      SELECT count(provider.numberOfNotificationsFailed.Sum)/count(provider.numberOfMessagesPublished.Sum) FROM QueueSample
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds
  warning {
    threshold_duration    = local.two_hours
    threshold             = 1 - var.sns_sms_failure_rate["warning"]
    operator              = local.newrelic_comparison_operator
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = local.two_hours
    threshold             = 1 - var.sns_sms_failure_rate["critical"] # current average rate is 0.5
    operator              = local.newrelic_comparison_operator
    threshold_occurrences = local.threshold_occurrences
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_phone_carrier_unavailable" {
  # WARN: More than local.phone_carrier_unavailable_threshold SMS failed because a phone carrier is unavailable over 1 hour.
  # CRIT: More than local.phone_carrier_unavailable_threshold SMS failed because a phone carrier is unavailable over 2 hours.

  name               = "${local.prefix}sns-sms-phone-carrier-unavailable"
  policy_id          = newrelic_alert_policy.pfml_aws_sns_high_priority_alert.id
  type               = local.condition_type
  value_function     = local.value_function
  enabled            = true
  aggregation_delay  = local.aggregation_delay
  aggregation_method = local.aggregation_method
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    #
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_log_group_name}' WHERE delivery.providerResponse = 'Phone carrier is currently unreachable/unavailable'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  warning {
    threshold_duration    = var.carrier_unavailable_period["warning"]
    threshold             = local.phone_carrier_unavailable_threshold # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator        # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = "at_least_once"
  }

  critical {
    threshold_duration    = var.carrier_unavailable_period["critical"]
    threshold             = local.phone_carrier_unavailable_threshold # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator        # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = local.threshold_occurrences
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_blocked_as_spam" {
  # More than 10 SMS have been blocked as spam over 2 hours.

  name               = "${local.prefix}sns-sms-blocked-as-spam"
  policy_id          = newrelic_alert_policy.pfml_aws_sns_high_priority_alert.id
  type               = local.condition_type
  value_function     = local.value_function
  enabled            = true
  aggregation_delay  = local.aggregation_delay
  aggregation_method = local.aggregation_method
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {

    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_log_group_name}' WHERE delivery.providerResponse = 'Blocked as spam by phone carrier'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  critical {
    threshold_duration    = local.two_hours                    # period in aws_cloudwatch_metric_alarm
    threshold             = local.blocked_as_spam_threshold    # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = local.threshold_occurrences
  }
}

resource "newrelic_nrql_alert_condition" "sns_sms_rate_exceeded" {
  # At least 1 SNS SMS rate exceeded error in 5 minutes

  name               = "${local.prefix}sns-sms-rate-exceeded"
  policy_id          = newrelic_alert_policy.pfml_aws_sns_high_priority_alert.id
  type               = local.condition_type
  value_function     = local.value_function
  enabled            = true
  aggregation_delay  = local.aggregation_delay
  aggregation_method = local.aggregation_method
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_log_group_name}' WHERE delivery.providerResponse = 'Rate exceeded'
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  critical {
    threshold_duration    = local.default_aggregation_window   # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 1                                  # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = local.threshold_occurrences
  }
}

resource "newrelic_nrql_alert_condition" "sns_mfa_delivery_time_exceeded" {
  # MFA delivery time (dwellTimeMs) exceeded 1 second over 5 minutes

  name               = "${local.prefix}sns-mfa-delivery-time-exceeded"
  policy_id          = newrelic_alert_policy.pfml_aws_sns_low_priority_alert.id
  type               = local.condition_type
  value_function     = local.value_function
  enabled            = true
  aggregation_delay  = local.aggregation_delay
  aggregation_method = local.aggregation_method
  aggregation_window = local.default_aggregation_window # (evaluation_periods * period) in aws_cloudwatch_metric_alarm

  nrql {
    query = <<-NRQL
      SELECT count(*) FROM Log WHERE aws.logGroup = '${local.sns_log_group_name}' WHERE (delivery.dwellTimeMsUntilDeviceAck >= ${local.mfa_user_response_time}) OR (delivery.dwellTimeMs >= ${local.mfa_sns_delivery_time})
    NRQL
  }

  violation_time_limit_seconds = local.violation_time_limit_seconds

  warning {
    threshold_duration    = local.default_aggregation_window   # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 1                                  # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = local.threshold_occurrences
  }

  critical {
    threshold_duration    = local.default_aggregation_window   # evaluation_periods in aws_cloudwatch_metric_alarm
    threshold             = 10                                 # threshold in aws_cloudwatch_metric_alarm
    operator              = local.newrelic_comparison_operator # comparison_operator in aws_cloudwatch_metric_alarm
    threshold_occurrences = local.threshold_occurrences
  }
}
