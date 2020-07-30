locals {
  ssm_arn_prefix         = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service"
  iam_db_user_arn_prefix = "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${data.aws_db_instance.default.resource_id}"
}

data "aws_iam_policy_document" "ecs_tasks_assume_role_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Task runtime role. This role is used by the task after it has started up -- i.e. for application-level access to AWS resources.
resource "aws_iam_role" "ecs_tasks" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks"

  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

data "aws_iam_policy_document" "db_user_pfml_api" {
  # Policy to allow connection to RDS via IAM database authentication as pfml_api user
  # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.IAMPolicy.html
  statement {
    actions = [
      "rds-db:connect"
    ]

    resources = [
      "${local.iam_db_user_arn_prefix}/pfml_api"
    ]
  }
}

resource "aws_iam_policy" "db_user_pfml_api" {
  name   = "${local.app_name}-${var.environment_name}-db_user_pfml_api-policy"
  policy = data.aws_iam_policy_document.db_user_pfml_api.json
}

resource "aws_iam_role_policy_attachment" "db_user_pfml_api_to_ecs_tasks_attachment" {
  role       = aws_iam_role.ecs_tasks.name
  policy_arn = aws_iam_policy.db_user_pfml_api.arn
}

# Task execution role. This role is used by ECS during startup to pull container images from
# ECR and access secrets from Systems Manager Parameter Store before running the application.
#
# See: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
resource "aws_iam_role" "task_executor" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-executor"

  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

data "aws_iam_policy_document" "task_executor" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      aws_cloudwatch_log_group.db_migrate_logs.arn,
      aws_cloudwatch_log_group.create_db_users_logs.arn
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*"
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}"
    ]
  }
}

# Link access policies to the ECS task execution role.
resource "aws_iam_role_policy" "task_executor" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-execution-role-policy"
  role   = aws_iam_role.task_executor.id
  policy = data.aws_iam_policy_document.task_executor.json
}
