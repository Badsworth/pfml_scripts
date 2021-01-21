# Terraform configuration for infrastructure-layer alarms. (host-specific metrics, e.g. CPU and RAM usage)

resource "aws_cloudwatch_metric_alarm" "api_cpu_warn" {
  count             = var.enable_alarm_api_cpu ? 1 : 0
  alarm_name        = "${local.app_name}-${var.environment_name}_CPU-Warning"
  alarm_description = "(${upper(var.environment_name)} API WARN) P95 CPU usage by API tasks exceeds 80%"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = "${local.app_name}-${var.environment_name}-server"
  }
  extended_statistic  = "p95"
  metric_name         = "CpuUtilized"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = (1024 * 0.80)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [var.warning_alert_sns_topic_arn]
  ok_actions          = [var.warning_alert_sns_topic_arn]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_metric_alarm" "api_cpu_crit" {
  count             = var.enable_alarm_api_cpu ? 1 : 0
  alarm_name        = "${local.app_name}-${var.environment_name}_CPU-Critical"
  alarm_description = "(${upper(var.environment_name)} API CRIT) P95 CPU usage by API tasks exceeds 90%"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = "${local.app_name}-${var.environment_name}-server"
  }
  extended_statistic  = "p95"
  metric_name         = "CpuUtilized"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = (1024 * 0.9)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [var.critical_alert_sns_topic_arn]
  ok_actions          = [var.critical_alert_sns_topic_arn]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "api_ram_warn" {
  count             = var.enable_alarm_api_ram ? 1 : 0
  alarm_name        = "${local.app_name}-${var.environment_name}_RAM-Warning"
  alarm_description = "(${upper(var.environment_name)} API WARN) P95 RAM usage by API tasks exceeds 90% container allotment"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = "${local.app_name}-${var.environment_name}-server"
  }
  extended_statistic  = "p95"
  metric_name         = "MemoryUtilized" # units: MiB
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = (2048 * 0.90)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [var.warning_alert_sns_topic_arn]
  ok_actions          = [var.warning_alert_sns_topic_arn]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_metric_alarm" "api_ram_crit" {
  count             = var.enable_alarm_api_ram ? 1 : 0
  alarm_name        = "${local.app_name}-${var.environment_name}_RAM-Critical"
  alarm_description = "(${upper(var.environment_name)} API CRIT) P95 RAM usage by API tasks exceeds 95% container allotment"
  namespace         = "ECS/ContainerInsights"
  dimensions = {
    ClusterName          = var.environment_name
    TaskDefinitionFamily = "${local.app_name}-${var.environment_name}-server"
  }
  extended_statistic  = "p95"
  metric_name         = "MemoryUtilized" # units: MiB
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = (2048 * 0.95)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [var.critical_alert_sns_topic_arn]
  ok_actions          = [var.critical_alert_sns_topic_arn]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# ----------------------------------------------------------------------------------------------------------------------

