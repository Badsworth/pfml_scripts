
resource "aws_cloudwatch_log_metric_filter" "aws_resource_changes" {
  name           = var.metric_name
  pattern        = var.pattern
  log_group_name = data.aws_cloudwatch_log_group.aws_resource_changes.name

  metric_transformation {
    name          = var.metric_name
    namespace     = var.namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "sns_resource_changes" {
  alarm_name          = var.alarm_name
  alarm_description   = var.alarm_description
  comparison_operator = var.comparison_operator
  evaluation_periods  = var.evaluation_periods
  metric_name         = aws_cloudwatch_log_metric_filter.aws_resource_changes.name
  namespace           = var.namespace
  period              = var.periods
  statistic           = var.statistic
  threshold           = var.threshold
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.sns_topic]
}

data "aws_cloudwatch_log_group" "aws_resource_changes" {
  name = "CloudTrail-PFML-498823821309"
}


