#
# Terraform configuration for IAM roles.
#

locals {
  ssm_arn_prefix = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service"
}

# Boilerplate policy to allow an IAM role to perform ECS tasks.
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

# Task execution role. This role is used by ECS to pull container images from
# ECR and access secrets from Systems Manager Parameter Store before running the application.
#
# See: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
resource "aws_iam_role" "task_executor" {
  name = "${local.app_name}-${var.environment_name}-task-executor"

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
      aws_cloudwatch_log_group.service_logs.arn,
      aws_cloudwatch_log_group.db_migrate_logs.arn,
      aws_cloudwatch_log_group.create_rds_user_logs.arn
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
  name   = "${local.app_name}-${var.environment_name}-task-execution-role-policy"
  role   = aws_iam_role.task_executor.id
  policy = data.aws_iam_policy_document.task_executor.json
}

# IAM role for allowing RDS instance to send monitoring insights to cloudwatch.
# Pulled from https://github.com/terraform-aws-modules/terraform-aws-rds/
#
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name_prefix        = "rds-enhanced-monitoring-${var.environment_name}-"
  assume_role_policy = data.aws_iam_policy_document.rds_enhanced_monitoring.json
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

data "aws_iam_policy_document" "rds_enhanced_monitoring" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}

# IAM role for lambda functions.
resource "aws_iam_role" "lambda_role" {
  name_prefix        = "massgov-pfml-${var.environment_name}-lambda-role-"
  assume_role_policy = data.aws_iam_policy_document.iam_policy_lambda_assumed_role.json
}

data "aws_iam_policy_document" "iam_policy_lambda_assumed_role" {
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

# Execution role policy for lambdas.
# Grants access to:
# - Cloudwatch
# - Specific s3 folders
# - Ability to create EC2 network interfaces (ENI) to execute lambda within a VPC
#
resource "aws_iam_role_policy" "lambda_execution" {
  name   = "massgov-pfml-${var.environment_name}-lambda_execution_role"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.iam_policy_lambda_execution.json
}

data "aws_iam_policy_document" "iam_policy_lambda_execution" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:*:*:*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParametersByPath"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}"
    ]
  }
}

# The role that the PFML API assumes to perform actions within AWS.
resource "aws_iam_role" "api_service" {
  name               = "${local.app_name}-${var.environment_name}-api-service"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# IAM policy that defines access rights to the S3 document upload buckets.
data "aws_iam_policy_document" "document_upload" {

  statement {
    sid = "AllowDocumentUploads"

    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:ListBucketMultipartUploads",
      "s3:ListMultipartUploadParts",
      "s3:DeleteObject"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-document",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-document/*"
    ]

    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.api_service.arn]
    }
  }

  # TODO: build an explicit deny policy, being mindful of admin rights
  #  statement {
  #    effect = "Deny"
  #  }
}
