data "aws_ecs_cluster" "cluster" { cluster_name = var.environment_name }

# Cloudwatch log group to for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "ecs_tasks" {
  name = "service/${local.app_name}-${var.environment_name}/ecs-tasks"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

locals {
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = module.constants.newrelic_log_ingestion_arn
}

resource "aws_cloudwatch_log_subscription_filter" "ecs_task_logging" {
  name            = "ecs_task_logs"
  log_group_name  = aws_cloudwatch_log_group.ecs_tasks.name
  destination_arn = local.newrelic_log_ingestion_lambda
  # matches all log events
  filter_pattern = ""
}

resource "aws_lambda_permission" "ecs_permission_tasks_logging" {
  statement_id  = "NRLambdaPermission_ECSTasksLogging_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
}

# ----------------------------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "every_15_minutes" {
  name                = "register-admins-${var.environment_name}-every-15-minutes"
  description         = "Fires every 15 minutes"
  schedule_expression = "rate(15 minutes)"
  is_enabled          = var.enable_register_admins_job
}

resource "aws_cloudwatch_event_target" "register_admins_event_target_ecs" {
  arn       = data.aws_ecs_cluster.cluster.arn
  target_id = "register_admins_${var.environment_name}_ecs_event_target"
  rule      = aws_cloudwatch_event_rule.every_15_minutes.name
  role_arn  = aws_iam_role.cloudwatch_events_register_admins_role.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.ecs_tasks["register-leave-admins-with-fineos"].arn
    launch_type         = "FARGATE"
    platform_version    = "1.4.0"

    network_configuration {
      assign_public_ip = false
      subnets          = var.app_subnet_ids
      security_groups  = [aws_security_group.tasks.id]
    }
  }
}
# -- Export daily registered users via execute-sql ------------------------------------------

resource "aws_cloudwatch_event_rule" "every_24_hours" {
  name                = "export-leave-admins-created-${var.environment_name}-every-24-hours"
  description         = "Fires every 24 hours"
  schedule_expression = "rate(24 hours)"
}

resource "aws_cloudwatch_event_target" "export_leave_admins_created_target_ecs" {
  arn       = data.aws_ecs_cluster.cluster.arn
  target_id = "export_leave_admins_${var.environment_name}_ecs_event_target"
  rule      = aws_cloudwatch_event_rule.every_24_hours.name
  role_arn  = aws_iam_role.cloudwatch_events_export_leave_admins_created_role.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.ecs_tasks["execute-sql"].arn
    launch_type         = "FARGATE"
    platform_version    = "1.4.0"

    network_configuration {
      assign_public_ip = false
      subnets          = var.app_subnet_ids
      security_groups  = [aws_security_group.tasks.id]
    }
  }
  input = <<DOC
{
  "containerOverrides": [
          {
            "name": "execute-sql",
            "command": [
              "execute-sql",
              "--s3_output=api_db/accounts_created",
              "--s3_bucket=massgov-pfml-${var.environment_name}-business-intelligence-tool",
              "--use_date",
              "SELECT pu.email_address as email, pu.user_id as user_id, pu.active_directory_id as cognito_id,ula.fineos_web_id as fineos_id,e.employer_name as employer_name,e.employer_dba as employer_dba,e.employer_fein as fein,e.fineos_employer_id as fineos_customer_number,ula.created_at as date_created FROM public.user pu LEFT JOIN link_user_leave_administrator ula ON (pu.user_id=ula.user_id) LEFT JOIN employer e ON (ula.employer_id=e.employer_id) WHERE ula.created_at >= now() - interval '24 hour'"
            ]
          }
        ]
}
DOC
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Payments ECS Task using Cloudwatch Events (Eventbridge)
resource "aws_cloudwatch_event_target" "trigger_payments_ctr_process_ecs_task_daily_at_9_am_et" {
  count = var.enable_recurring_payments_schedule == true ? 1 : 0

  rule      = aws_cloudwatch_event_rule.payments_ctr_process_ecs_task_daily_at_9_am_et.name
  arn       = data.aws_ecs_cluster.cluster.arn
  target_id = "payments_ctr_process_${var.environment_name}_cloudwatch_event_target"
  role_arn  = aws_iam_role.cloudwatch_events_payments_ctr_scheduler_role.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.ecs_tasks["payments-ctr-process"].arn
    launch_type         = "FARGATE"
    platform_version    = "1.4.0"

    network_configuration {
      assign_public_ip = false
      subnets          = var.app_subnet_ids
      security_groups  = [aws_security_group.tasks.id]
    }
  }
}

resource "aws_cloudwatch_event_rule" "payments_ctr_process_ecs_task_daily_at_9_am_et" {
  name        = "${var.environment_name}-payments-ctr-process-ecs-task-daily-at-9-am-et"
  description = "Fires the ${var.environment_name} Payments CTR Process ECS task daily at 9am US EDT/2pm UTC"
  # The time of day can only be specified in UTC and will need to be updated when daylight savings changes occur, if the 9AM US ET is desired to be consistent.
  schedule_expression = "cron(0 14 * * ? *)"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# payments-fineos-process task using Cloudwatch Events (Eventbridge)
resource "aws_cloudwatch_event_target" "trigger_payments_fineos_process_ecs_task_daily_at_8_pm_et" {
  count = var.enable_recurring_payments_schedule == true ? 1 : 0

  rule      = aws_cloudwatch_event_rule.payments_fineos_process_ecs_task_daily_at_8_pm_et.name
  arn       = data.aws_ecs_cluster.cluster.arn
  target_id = "payments_fineos_process_${var.environment_name}_cloudwatch_event_target"
  role_arn  = aws_iam_role.cloudwatch_events_payments_fineos_scheduler_role.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.ecs_tasks["payments-fineos-process"].arn
    launch_type         = "FARGATE"
    platform_version    = "1.4.0"

    network_configuration {
      assign_public_ip = false
      subnets          = var.app_subnet_ids
      security_groups  = [aws_security_group.tasks.id]
    }
  }
}

resource "aws_cloudwatch_event_rule" "payments_fineos_process_ecs_task_daily_at_8_pm_et" {
  name        = "${var.environment_name}-payments-fineos-process-ecs-task-daily-at-8-pm-et"
  description = "Fires the ${var.environment_name} Payments FINEOS Process ECS task daily at 8pm US EDT/1am UTC"
  # The time of day can only be specified in UTC and will need to be updated when daylight savings changes occur, if the 8PM US ET is desired to be consistent.
  schedule_expression = "cron(0 1 * * ? *)"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}
