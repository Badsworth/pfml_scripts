locals {
  ssm_arn_prefix = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service"
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
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
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

# ------------------------------------------------------------------------------------------------------
# Adhoc Task Policy Stuff
# ------------------------------------------------------------------------------------------------------


data "aws_iam_policy_document" "task_adhoc_executor_s3_policy_doc" {
  # Allow ECS Adhoc Verification task access S3 files
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-verification-codes",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-verification-codes/*"
    ]
  }
}

resource "aws_iam_role" "task_adhoc_verification_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-adhoc-verification-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}


resource "aws_iam_policy" "task_adhoc_executor_s3_policy" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-adhoc-verification-s3-policy"
  description = "Policy for accessing S3 files for ECS Ad-Hoc Verification Tasks"
  policy      = data.aws_iam_policy_document.task_adhoc_executor_s3_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "task_adhoc_task_executor_s3_attachment" {
  role       = aws_iam_role.task_adhoc_verification_task_role.name
  policy_arn = aws_iam_policy.task_adhoc_executor_s3_policy.arn
}
