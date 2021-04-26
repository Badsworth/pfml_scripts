resource "aws_iam_role" "task_trigger" {
  name               = "${var.task_name}-${var.environment_name}-task-trigger"
  assume_role_policy = data.aws_iam_policy_document.allow_lambda_assume_role.json
}

data "aws_iam_policy_document" "allow_lambda_assume_role" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }

  }
}

resource "aws_iam_role_policy" "task_trigger" {
  name   = "${var.task_name}-${var.environment_name}-task-trigger-role-policy"
  role   = aws_iam_role.task_trigger.id
  policy = data.aws_iam_policy_document.allow_task_trigger.json
}

data "aws_iam_policy_document" "allow_task_trigger" {
  statement {
    effect = "Allow"
    actions = [
      "ecs:RunTask",
      "ecs:StopTask",
      "ecs:DescribeTasks"
    ]
    resources = [
      "arn:aws:ecs:us-east-1:${data.aws_caller_identity.current.account_id}:task-definition/${var.ecs_task_definition_family}",
      "arn:aws:ecs:us-east-1:${data.aws_caller_identity.current.account_id}:task-definition/${var.ecs_task_definition_family}:*"
    ]
  }

  statement {
    effect  = "Allow"
    actions = ["iam:PassRole"]
    resources = [
      var.ecs_task_executor_role,
      var.ecs_task_role
    ]
  }
}

# Managed policy, granting permission to upload logs to CloudWatch
resource "aws_iam_role_policy_attachment" "task_trigger_basic_execution" {
  role       = aws_iam_role.task_trigger.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Grant access to launch lambdas in VPCs
resource "aws_iam_role_policy_attachment" "task_trigger_vpc_execution" {
  role       = aws_iam_role.task_trigger.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
