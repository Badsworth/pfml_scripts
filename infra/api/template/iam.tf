#
# Terraform configuration for IAM roles.
#

locals {
  ssm_arn_prefix         = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service"
  iam_db_user_arn_prefix = "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.default.resource_id}"
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
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.service_logs.arn}:*",
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
      "${local.ssm_arn_prefix}/${local.app_name}/common/*"
    ]
  }

  # Allow ECS to access secrets from parameter store in bulk.
  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}/common"
    ]
  }
}

data "aws_iam_policy_document" "document_upload_kms_key" {
  # Allow read/write with KMS key
  statement {
    sid = "AllowReadWriteForApiService"

    actions = [
      "kms:Encrypt",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]

    effect    = "Allow"
    resources = ["*"]

    condition {
      test     = "StringLike"
      variable = "aws:userId"

      values = [
        "${aws_iam_role.api_service.unique_id}:*"
      ]
    }

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }

  statement {
    sid = "AllowAllForAdmins"

    actions = [
      "kms:*",
    ]

    effect    = "Allow"
    resources = ["*"]

    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
        "arn:aws:iam::498823821309:role/AWS-498823821309-Infrastructure-Admin",
        "arn:aws:iam::498823821309:role/ci-run-deploys",
      ]
    }
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

#IAM role for Formstack import lambda
#name_prefix is highly abbreviated due to 32 character limit by Terraform
resource "aws_iam_role" "formstack_import_lambda_role" {
  name_prefix        = "massgov-pfml-${var.environment_name}-frmstk-role-"
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

# Execution role policy for the Formstack import lambda.
# Grants access to:
# - Cloudwatch
# - Specific s3 folders
# - Ability to create EC2 network interfaces (ENI) to execute lambda within a VPC
# - Has PutParameter access
resource "aws_iam_role_policy" "formstack_import_lambda_execution" {
  name   = "massgov-pfml-${var.environment_name}-formstack_import_lambda_execution_role"
  role   = aws_iam_role.formstack_import_lambda_role.id
  policy = data.aws_iam_policy_document.iam_policy_formstack_import_lambda_execution.json
}

data "aws_iam_policy_document" "iam_policy_formstack_import_lambda_execution" {
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
      data.aws_s3_bucket.formstack_import.arn,
      "${data.aws_s3_bucket.formstack_import.arn}/*"
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
      "ssm:GetParameters",
      "ssm:PutParameter",
      "ssm:PutParameters"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}-formstack-import/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParametersByPath"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}-formstack-import/*"
    ]
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
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}",
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

  statement {
    sid    = "DenyIncorrectEncryptionHeader"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::massgov-pfml-${var.environment_name}-document/*"]

    condition {
      test     = "StringNotEquals"
      variable = "s3:x-amz-server-side-encryption"
      values   = ["aws:kms"]
    }
  }

  statement {
    sid    = "DenyIncorrectIdProofingKey"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::massgov-pfml-${var.environment_name}-document/identity_proofing/*"]

    condition {
      test     = "StringNotLikeIfExists"
      variable = "s3:x-amz-server-side-encryption-aws-kms-key-id"
      values   = [aws_kms_key.id_proofing_document_upload_kms_key.arn]
    }
  }

  statement {
    sid    = "DenyIncorrectCertificationKey"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::massgov-pfml-${var.environment_name}-document/certification/*"]

    condition {
      test     = "StringNotLikeIfExists"
      variable = "s3:x-amz-server-side-encryption-aws-kms-key-id"
      values   = [aws_kms_key.certification_document_upload_kms_key.arn]
    }
  }

  # TODO: build an explicit deny policy, being mindful of admin rights
  #  statement {
  #    effect = "Deny"
  #  }
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

data "aws_iam_policy_document" "cloudtrail_logging" {
  statement {
    sid = "WriteCloudtrailLogs"

    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-cloudtrail-s3-logging/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
    ]
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }

  statement {
    sid = "CloudtrailAclCheck"

    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions = [
      "s3:GetBucketAcl"
    ]
    resources = ["arn:aws:s3:::massgov-pfml-${var.environment_name}-cloudtrail-s3-logging"]
  }
}

resource "aws_iam_policy" "db_user_pfml_api" {
  name   = "${local.app_name}-${var.environment_name}-db_user_pfml_api-policy"
  policy = data.aws_iam_policy_document.db_user_pfml_api.json
}

resource "aws_iam_role_policy_attachment" "db_user_pfml_api_to_api_service_attachment" {
  role       = aws_iam_role.api_service.name
  policy_arn = aws_iam_policy.db_user_pfml_api.arn
}

resource "aws_iam_role_policy_attachment" "db_user_pfml_api_to_lambda_role_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.db_user_pfml_api.arn
}

resource "aws_iam_role_policy_attachment" "db_user_pfml_api_to_formstack_lambda_role_attachment" {
  role       = aws_iam_role.formstack_import_lambda_role.name
  policy_arn = aws_iam_policy.db_user_pfml_api.arn
}