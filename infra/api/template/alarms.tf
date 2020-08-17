# Terraform configuration for all the alarms. All of them.

# ----------------------------------------------------------------------------------------------------------------------

# Defines an SNS topic for low-priority alerts.
resource "aws_sns_topic" "api-low-priority-alerts-topic" {
  name         = "api-low-priority-alerts-topic"
  display_name = "PFML API: Low Priority Alerts"
}

# Defines an SNS topic for high-priority alerts.
resource "aws_sns_topic" "api-high-priority-alerts-topic" {
  name         = "api-high-priority-alerts-topic"
  display_name = "PFML API: High Priority Alerts"
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "api_cpu_warn" {
  alarm_name        = "${local.app_name}-${var.environment_name}_CPU-Warning"
  alarm_description = "P95 CPU usage by API tasks exceeds 60%"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = local.app_name
  }
  extended_statistic  = "p95"
  metric_name         = "CpuUtilized"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = "60"
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.api-low-priority-alerts-topic.arn]
}

resource "aws_cloudwatch_metric_alarm" "api_cpu_crit" {
  alarm_name        = "${local.app_name}-${var.environment_name}_CPU-Critical"
  alarm_description = "P95 CPU usage by API tasks exceeds 80%"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = local.app_name
  }
  extended_statistic  = "p95"
  metric_name         = "CpuUtilized"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = "80"
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.api-high-priority-alerts-topic.arn]
  ok_actions          = [aws_sns_topic.api-high-priority-alerts-topic.arn]
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "api_ram_warn" {
  alarm_name        = "${local.app_name}-${var.environment_name}_RAM-Warning"
  alarm_description = "P95 RAM usage by API tasks exceeds 50% container allotment"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = local.app_name
  }
  extended_statistic  = "p95"
  metric_name         = "MemoryUtilized" # units: MiB
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = (data.template_file.container_definitions.vars.memory * 0.50)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.api-low-priority-alerts-topic.arn]
}

resource "aws_cloudwatch_metric_alarm" "api_ram_crit" {
  alarm_name        = "${local.app_name}-${var.environment_name}_RAM-Critical"
  alarm_description = "P95 RAM usage by API tasks exceeds 75% container allotment"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = local.app_name
  }
  extended_statistic  = "p95"
  metric_name         = "MemoryUtilized" # units: MiB
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = (data.template_file.container_definitions.vars.memory * 0.75)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.api-high-priority-alerts-topic.arn]
  ok_actions          = [aws_sns_topic.api-high-priority-alerts-topic.arn]
}

# ----------------------------------------------------------------------------------------------------------------------
