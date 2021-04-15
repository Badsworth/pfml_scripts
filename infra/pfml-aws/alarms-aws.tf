# CloudWatch alarms that apply to the entire AWS account at once.
locals {
  api_high_priority_alerts = "arn:aws:sns:us-east-1:498823821309:api-high-priority-alerts-topic"
  # ↑ this is aws_sns_topic.api-high-priority-alerts-topic.arn in module 'monitoring', brought in here as a raw ARN
}

# TODO: a "burn rate" metric: given a send rate and remaining send quota, how long until the entire quota is used up?
resource "aws_cloudwatch_metric_alarm" "ses_send_rate" {
  alarm_name = "ses_send_rate"
  alarm_description = "(SES CRIT) Abnormally high email send rate through SES"
  namespace = "AWS/SES"
  metric_name = "Send"

  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold = 300  # if 300 or more emails are sent in a single 'period'
  statistic = "Sum"
  evaluation_periods = "6" # look back at the last 30 minutes
  datapoints_to_alarm = "2" # any two five-minute periods
  period = "300" # five-minute aggregation window

  actions_enabled = true
  alarm_actions = [local.api_high_priority_alerts]

  # There should always be a send rate, even if it's zero.
  # If there's NO send rate, we've hit our send quota and NO environment can send any more emails from our AWS account.
  # Someone must get paged if this happens, because user sign-up is broken in prod if we can't send any emails.
  insufficient_data_actions = [local.api_high_priority_alerts]
  treat_missing_data = "breaching"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags["prod"]
  })
}
