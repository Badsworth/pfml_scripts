# CloudWatch alarms that apply to the entire AWS account at once.
locals {
  api_high_priority_alerts = "arn:aws:sns:us-east-1:498823821309:api-high-priority-alerts-topic"
  # ↑ this is aws_sns_topic.api-high-priority-alerts-topic.arn in module 'monitoring', brought in here as a raw ARN
}

# TODO: a "burn rate" metric: given a send rate and remaining send quota, how long until the entire quota is used up?
resource "aws_cloudwatch_metric_alarm" "ses_send_rate" {
  alarm_name        = "massgov_pfml_allenvs-ses_send_rate"
  alarm_description = "(SES CRIT) Abnormally high email send rate through SES"
  namespace         = "AWS/SES"
  metric_name       = "Send"

  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 500 # if 500 or more emails are sent in a single 'period'
  statistic           = "Sum"
  evaluation_periods  = "12"  # look back at the last hour
  datapoints_to_alarm = "9"   # any nine five-minute periods, e.g. 45 minutes in the last hour
  period              = "300" # five-minute aggregation window

  actions_enabled = true
  alarm_actions   = [local.api_high_priority_alerts]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags["prod"]
  })
}
