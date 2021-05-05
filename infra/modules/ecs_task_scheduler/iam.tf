resource "aws_iam_role" "scheduler" {
  name               = "${var.schedule_name}-${var.environment_name}-scheduler"
  assume_role_policy = data.aws_iam_policy_document.cloudwatch_events_assume_role_policy.json
}

data "aws_iam_policy_document" "cloudwatch_events_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "scheduler_role_policy" {
  name   = "${var.schedule_name}-${var.environment_name}-scheduler-role-policy"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler_role_policy.json
}

data "aws_iam_policy_document" "scheduler_role_policy" {
  statement {
    effect  = "Allow"
    actions = ["ecs:RunTask"]

    resources = ["arn:aws:ecs:us-east-1:${data.aws_caller_identity.current.account_id}:task-definition/${var.ecs_task_definition_family}:*"]
  }

  statement {
    effect  = "Allow"
    actions = ["iam:PassRole"]

    resources = compact([
      var.ecs_task_executor_role,
      var.ecs_task_role
    ])
  }
}
