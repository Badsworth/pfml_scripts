# Terraform configuration for infrastructure-layer alarms. (host-specific metrics, e.g. CPU and RAM usage)

locals {
  critical_sns_topic = {
    "test"        = aws_sns_topic.api-low-priority-alerts-topic.arn
    "stage"       = aws_sns_topic.api-low-priority-alerts-topic.arn
    "performance" = aws_sns_topic.api-low-priority-alerts-topic.arn
    "training"    = aws_sns_topic.api-low-priority-alerts-topic.arn
    "uat"         = aws_sns_topic.api-low-priority-alerts-topic.arn
    "prod"        = aws_sns_topic.api-high-priority-alerts-topic.arn
  }
}

# ----------------------------------------------------------------------------------------------------------------------

# Defines an SNS topic for low-priority alerts.
resource "aws_sns_topic" "api-low-priority-alerts-topic" {
  name         = "api-low-priority-alerts-topic"
  display_name = "PFML API: Low Priority Alerts"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
  })
}

# Defines an SNS topic for high-priority alerts.
resource "aws_sns_topic" "api-high-priority-alerts-topic" {
  name         = "api-high-priority-alerts-topic"
  display_name = "PFML API: High Priority Alerts"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
  })
}

# Defines SNS topic subscriptions for AWS Cloudwatch
resource "aws_sns_topic_subscription" "low-priority" {
  topic_arn              = aws_sns_topic.api-low-priority-alerts-topic.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${data.terraform_remote_state.pagerduty.outputs.low_priority_cloudwatch_integration_key}/enqueue"
  endpoint_auto_confirms = true
}

resource "aws_sns_topic_subscription" "high-priority" {
  topic_arn              = aws_sns_topic.api-high-priority-alerts-topic.arn
  protocol               = "https"
  endpoint               = "https://events.pagerduty.com/integration/${data.terraform_remote_state.pagerduty.outputs.high_priority_cloudwatch_integration_key}/enqueue"
  endpoint_auto_confirms = true
}
# ----------------------------------------------------------------------------------------------------------------------

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
  threshold           = (data.template_file.container_definitions.vars.cpu * 0.80)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.api-low-priority-alerts-topic.arn]
  ok_actions          = [aws_sns_topic.api-low-priority-alerts-topic.arn]

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
  threshold           = (data.template_file.container_definitions.vars.cpu * 0.90)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [local.critical_sns_topic[var.environment_name]]
  ok_actions          = [local.critical_sns_topic[var.environment_name]]

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
  threshold           = (data.template_file.container_definitions.vars.memory * 0.90)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.api-low-priority-alerts-topic.arn]
  ok_actions          = [aws_sns_topic.api-low-priority-alerts-topic.arn]

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
  threshold           = (data.template_file.container_definitions.vars.memory * 0.95)
  evaluation_periods  = "5"  # look back at the last five minutes
  datapoints_to_alarm = "3"  # any three one-minute periods
  period              = "60" # polling on one-minute intervals
  actions_enabled     = true
  alarm_actions       = [local.critical_sns_topic[var.environment_name]]
  ok_actions          = [local.critical_sns_topic[var.environment_name]]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# ----------------------------------------------------------------------------------------------------------------------

