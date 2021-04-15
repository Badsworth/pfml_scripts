
locals {
  alarm_names = [
    "export-leave-admins-created",
    "fineos-error-extract-tool",
    "fineos-data-export-tool",
    "reductions-retrieve-payment-lists",
    "reductions-send-wage-replacement",
    "reductions-send-claimant-lists"
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
    rule_name = "${each.key}_${var.environment_name}_schedule"
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

# ----------------------------------------------------------------------------------------------------------------------

# TODO: a "burn rate" metric: given a send rate and remaining send quota, how long until the entire quota is used up?
# TODO: this alarm must not be unique by environment; SES send rate metrics and quotas are account-wide
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
  alarm_actions = [var.critical_alert_sns_topic_arn]

  # There should always be a send rate, even if it's zero.
  # If there's NO send rate, we've hit our send quota and NO environment can send any more emails from our AWS account.
  # Someone must get paged if this happens, because user sign-up is broken in prod if we can't send any emails.
  insufficient_data_actions = [var.critical_alert_sns_topic_arn]
  treat_missing_data = "breaching"

  tags = module.constants.common_tags
}