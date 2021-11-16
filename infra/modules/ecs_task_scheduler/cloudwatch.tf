resource "aws_cloudwatch_event_target" "task" {
  rule      = aws_cloudwatch_event_rule.scheduled_rule.name
  arn       = var.cluster_arn
  target_id = "${var.task_name}_${module.constants.environment_shorthand[var.environment_name]}_cloudwatch_event_target"
  role_arn  = aws_iam_role.scheduler.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = var.ecs_task_definition_arn
    launch_type         = "FARGATE"
    platform_version    = "1.4.0"

    network_configuration {
      assign_public_ip = false
      subnets          = var.app_subnet_ids
      security_groups  = var.security_group_ids
    }
  }

  input = var.input
}

locals {
  is_daylight_savings = false
}

resource "aws_cloudwatch_event_rule" "scheduled_rule" {
  name        = "${var.task_name}_${var.environment_name}_schedule"
  description = "Fires the ${var.task_name} task in ${var.environment_name} on a schedule"

  is_enabled          = var.is_enabled
  schedule_expression = local.is_daylight_savings ? var.schedule_expression_daylight_savings : var.schedule_expression_standard

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}
