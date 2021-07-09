
locals {
  alarm_names = [
    "export-leave-admins-created",
    "fineos-error-extract-tool",
    "fineos-data-export-tool",
    "fineos-report-extracts-tool",
    "reductions-retrieve-payment-lists",
    "reductions-send-wage-replacement",
    "reductions-dua-send-claimant-lists",
    "reductions-dia-send-claimant-lists",
    "dor-fineos-etl",
    "import-fineos-to-warehouse",
    "payments-payment-voucher-plus",
    "process-cps-error-reports",
    "weekend-cps-extract-processing",
    "pub-payments-process-fineos",
    "weekend-pub-claimant-extract"
  ]
}


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

resource "aws_cloudwatch_metric_alarm" "failed_invocations" {

  for_each = toset(local.alarm_names)

  alarm_name        = "failed ${each.key}_${var.environment_name}_schedule_alert"
  alarm_description = "(${upper(var.environment_name)} API CRIT) ${each.key} failed to start"
  namespace         = "AWS/Events"
  dimensions = {
    RuleName = "${each.key}_${var.environment_name}_schedule"
  }

  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  metric_name         = "FailedInvocations"
  statistic           = "Sum"
  evaluation_periods  = "5" # look back at the last five minutes
  datapoints_to_alarm = "1" # any three one-minute periods
  period              = "60"
  actions_enabled     = true
  alarm_actions       = [var.warning_alert_sns_topic_arn]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}
