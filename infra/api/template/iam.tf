#
# Terraform configuration for IAM roles.
#

# Task execution role. This role is used by ECS to pull container images from
# ECR and access secrets from Systems Manager Parameter Store before running the application.
#
# See: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
resource "aws_iam_role" "task_executor" {
  name = "${local.app_name}-${var.environment_name}-task-executor"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
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
      aws_cloudwatch_log_group.service_logs.arn
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
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service/${local.app_name}/${var.environment_name}/*"
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service/${local.app_name}/${var.environment_name}"
    ]
  }
}

# Link access policies to the ECS task execution role.
resource "aws_iam_role_policy" "task_executor" {
  name   = "${local.app_name}-${var.environment_name}-task-execution-role-policy"
  role   = aws_iam_role.task_executor.id
  policy = data.aws_iam_policy_document.task_executor.json
}
