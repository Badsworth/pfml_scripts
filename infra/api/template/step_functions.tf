#
# Terraform configuration for AWS Step Functions.
#

#
# State machine for daily DOR FINEOS ETL.
#
resource "aws_sfn_state_machine" "dor_fineos_etl" {
  name       = "${local.app_name}-${var.environment_name}-dor-fineos-etl"
  role_arn   = aws_iam_role.step_functions_execution.arn
  definition = var.dor_fineos_etl_definition

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}


# This is defined in ecs-tasks/template/security_groups.tf and referenced by name here.
data "aws_security_group" "tasks" {
  name = "${local.app_name}-${var.environment_name}-tasks"
}

# This is defined in ecs-tasks/template/sns.tf and referenced by name here.
data "aws_sns_topic" "task_failure" {
  name = "mass-pfml-${var.environment_name}-task-failure"
}

# These are defined in ecs-tasks/template/iam.tf and referenced by name here.
data "aws_iam_role" "dor_import_task_role" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-task-role"
}

data "aws_iam_role" "dor_import_execution_role" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-execution-role"
}

data "aws_iam_role" "ecs_tasks_task_role" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks"
}

data "aws_iam_role" "ecs_tasks_execution_role" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-execution-role"
}

data "aws_iam_role" "fineos_import_employee_updates_task_role" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-employee-updates"
}

data "aws_iam_role" "fineos_eligibility_feed_export_task_role" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-eligibility-feed-export"
}
resource "aws_iam_role" "step_functions_execution" {
  name               = "${local.app_name}-${var.environment_name}-step-functions"
  assume_role_policy = data.aws_iam_policy_document.step_functions_execution.json
}
data "aws_iam_policy_document" "step_functions_execution" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "step_functions_execution" {
  name   = "${local.app_name}-${var.environment_name}-step-functions-role-policy"
  role   = aws_iam_role.step_functions_execution.id
  policy = data.aws_iam_policy_document.iam_policy_step_functions.json
}

data "aws_iam_policy_document" "iam_policy_step_functions" {
  statement {
    effect = "Allow"
    actions = [
      "ecs:RunTask",
      "ecs:StopTask",
      "ecs:DescribeTasks"
    ]
    resources = ["*"]
  }

  statement {
    effect  = "Allow"
    actions = ["iam:PassRole"]
    resources = [
      aws_iam_role.task_executor.arn,
      data.aws_iam_role.dor_import_task_role.arn,
      data.aws_iam_role.dor_import_execution_role.arn,
      data.aws_iam_role.ecs_tasks_task_role.arn,
      data.aws_iam_role.ecs_tasks_execution_role.arn,
      data.aws_iam_role.fineos_import_employee_updates_task_role.arn,
      data.aws_iam_role.fineos_eligibility_feed_export_task_role.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "events:PutTargets",
      "events:PutRule",
      "events:DescribeRule"
    ]
    resources = [
      "arn:aws:events:us-east-1:${data.aws_caller_identity.current.account_id}:rule/StepFunctionsGetEventsForECSTaskRule"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "sns:Publish",
    ]
    resources = [
      data.aws_sns_topic.task_failure.arn
    ]
  }
}

#
# Scheduling using EventBridge (previously called CloudWatch Events).
#

resource "aws_cloudwatch_event_rule" "dor_fineos_etl" {
  name                = "dor-fineos-etl-${var.environment_name}-schedule"
  description         = "Schedule dor-fineos-etl step function"
  schedule_expression = var.dor_fineos_etl_schedule_expression
}

resource "aws_cloudwatch_event_target" "dor_fineos_etl_event_target_ecs" {
  rule      = aws_cloudwatch_event_rule.dor_fineos_etl.name
  arn       = aws_sfn_state_machine.dor_fineos_etl.arn
  target_id = "dor_fineos_etl_${var.environment_name}_step_function_target"
  role_arn  = aws_iam_role.eventbridge_step_functions.arn
}

# Role that allows EventBridge to start Step Functions.
resource "aws_iam_role" "eventbridge_step_functions" {
  name               = "${local.app_name}-${var.environment_name}-eventbridge-step-functions"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_step_functions.json
}

data "aws_iam_policy_document" "eventbridge_step_functions" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "eventbridge_step_functions_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-eventbridge-step-functions-role-policy"
  role   = aws_iam_role.eventbridge_step_functions.name
  policy = data.aws_iam_policy_document.eventbridge_step_functions_role_policy_document.json
}

data "aws_iam_policy_document" "eventbridge_step_functions_role_policy_document" {
  statement {
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.dor_fineos_etl.arn]
  }
}
