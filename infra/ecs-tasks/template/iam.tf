# IAM roles and permissions for ECS tasks.

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
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-execution-role"

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

# ------------------------------------------------------------------------------------------------------
# User Bulk Import task stuff
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "task_bulk_import_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-bulk-import-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

data "aws_iam_policy_document" "task_bulk_import_s3_policy_doc" {
  # Allow ECS User Bulk Import task access S3 files
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-bulk-user-import",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-bulk-user-import/*"
    ]
  }
}

resource "aws_iam_policy" "task_bulk_import_s3_policy" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-bulk-import-task-s3-policy"
  description = "Policy for accessing S3 files for Bulk Import Tasks"
  policy      = data.aws_iam_policy_document.task_bulk_import_s3_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "task_import_s3_policy_attachment" {
  role       = aws_iam_role.task_bulk_import_task_role.name
  policy_arn = aws_iam_policy.task_bulk_import_s3_policy.arn
}


data "aws_iam_policy_document" "task_import_cognito_doc" {
  # Allow ECS User Bulk Import task access to Cognito IDP
  statement {
    actions = [
      "cognito-idp:ListUsers",
      "cognito-idp:AdminCreateUser",
      "cognito-idp:AdminSetUserPassword"
    ]

    resources = [
      "arn:aws:cognito-idp:us-east-1:498823821309:userpool/${var.cognito_user_pool_id}"
    ]
  }
}

resource "aws_iam_policy" "task_import_cognito_policy" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-bulk-import-task-cognito-policy"
  description = "Policy for accessing Cognito for ECS Bulk User Import Tasks"
  policy      = data.aws_iam_policy_document.task_import_cognito_doc.json
}

resource "aws_iam_role_policy_attachment" "task_import_cognito_policy_attachment" {
  role       = aws_iam_role.task_bulk_import_task_role.name
  policy_arn = aws_iam_policy.task_import_cognito_policy.arn
}


# ------------------------------------------------------------------------------------------------------
# Execute SQL Export Task Stuff
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "task_execute_sql_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-execute-sql-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

data "aws_iam_policy_document" "task_sql_export_s3_policy_doc" {
  # Allow Execute SQL task access to WRITE S3 files
  statement {
    actions = [
      "s3:PutObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export/*"
    ]
  }
}

resource "aws_iam_policy" "task_execute_sql_s3_policy" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-execute-sql-s3-policy"
  description = "Policy for accessing S3 files Execute SQL Tasks"
  policy      = data.aws_iam_policy_document.task_sql_export_s3_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "task_execute_sql_s3_attachment" {
  role       = aws_iam_role.task_execute_sql_task_role.name
  policy_arn = aws_iam_policy.task_execute_sql_s3_policy.arn
}

# ------------------------------------------------------------------------------------------------------
# DOR Import task stuff
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "dor_import_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "dor_import_task_role_extras" {
  role       = aws_iam_role.dor_import_task_role.name
  policy_arn = aws_iam_policy.dor_import_task_role_extras.arn
}

resource "aws_iam_policy" "dor_import_task_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-ecs-policy"
  description = "All the things the DOR Import task needs to be allowed to do"
  policy      = data.aws_iam_policy_document.dor_import_task_role_extras.json
}

data "aws_iam_policy_document" "dor_import_task_role_extras" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

resource "aws_iam_role" "dor_import_execution_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "dor_import_execution_role_extras" {
  role       = aws_iam_role.dor_import_execution_role.name
  policy_arn = aws_iam_policy.dor_import_execution_role_extras.arn
}

resource "aws_iam_policy" "dor_import_execution_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-execution-policy"
  description = "A clone of the standard execution role with extra SSM permissions for DOR Import's decryption keys."
  policy      = data.aws_iam_policy_document.dor_import_execution_role_extras.json
}

data "aws_iam_policy_document" "dor_import_execution_role_extras" {
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
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}/*"
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}"
    ]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for FINEOS Eligibility Feed export
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "fineos_eligibility_feed_export_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-eligibility-feed-export"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "fineos_eligibility_feed_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-eligibility-feed-export-fineos-policy"
  role   = aws_iam_role.fineos_eligibility_feed_export_task_role.id
  policy = data.aws_iam_policy_document.fineos_eligibility_feed_export_fineos_role_policy[0].json
}

data "aws_iam_policy_document" "fineos_eligibility_feed_export_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  statement {

    effect = "Allow"

    actions = [
      "sts:AssumeRole",
    ]

    resources = [
      var.fineos_aws_iam_role_arn,
    ]
  }
}
