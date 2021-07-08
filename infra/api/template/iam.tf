#
# Terraform configuration for IAM roles.
#

locals {
  ssm_arn_prefix         = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service"
  iam_db_user_arn_prefix = "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.default.resource_id}"
  shorthand_env_name     = module.constants.environment_shorthand[var.environment_name]
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM stuff for ECS
# ----------------------------------------------------------------------------------------------------------------------

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

# Link access policies to the ECS task execution role.
resource "aws_iam_role_policy" "task_executor" {
  name   = "${local.app_name}-${var.environment_name}-task-execution-role-policy"
  role   = aws_iam_role.task_executor.id
  policy = data.aws_iam_policy_document.task_executor.json
}

# ----------------------------------------------------------------------------------------------------------------------
# Paid Leave API ECS service

# The role that the PFML API assumes to perform actions within AWS.
resource "aws_iam_role" "api_service" {
  name               = "${local.app_name}-${var.environment_name}-api-service"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "db_user_pfml_api_to_api_service_attachment" {
  role       = aws_iam_role.api_service.name
  policy_arn = aws_iam_policy.db_user_pfml_api.arn
}

resource "aws_iam_role_policy" "api_service" {
  name   = "${local.app_name}-${var.environment_name}-api-service-policy"
  role   = aws_iam_role.api_service.id
  policy = data.aws_iam_policy_document.api_service.json
}

# Temporary additions for Feature Gate S3 access

resource "aws_iam_role_policy" "feature_gate_s3_access" {
  name   = "${local.app_name}-${var.environment_name}-feature-gate-s3-access-policy"
  role   = aws_iam_role.api_service.id
  policy = data.aws_iam_policy_document.feature_gate.json
}


data "aws_iam_policy_document" "api_service" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      var.rmv_client_certificate_binary_arn,
    ]
  }

  # Conditionally add permissions to talk to Cognito if its been
  # configured. We may not have one yet if we're starting up a new environment.
  dynamic "statement" {
    for_each = var.cognito_user_pool_arn == null ? [] : [1]
    content {
      effect = "Allow"
      actions = [
        "cognito-idp:AdminGetUser",
      ]
      resources = [
        var.cognito_user_pool_arn
      ]
    }
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM stuff for Lambdas
# ----------------------------------------------------------------------------------------------------------------------

# Shared assume_role_policy doc for all Lambdas
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


# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for FINEOS Eligibility Feed Lambda

resource "aws_iam_role" "eligibility_feed_lambda_role" {
  name_prefix        = "massgov-pfml-${local.shorthand_env_name}-ef-lmbd-role-"
  assume_role_policy = data.aws_iam_policy_document.iam_policy_lambda_assumed_role.json
}

resource "aws_iam_role_policy_attachment" "eligibility_feed_lambda_role_vpc_execution" {
  role       = aws_iam_role.eligibility_feed_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "db_user_pfml_api_to_eligibility_feed_lambda_role_attachment" {
  role       = aws_iam_role.eligibility_feed_lambda_role.name
  policy_arn = aws_iam_policy.db_user_pfml_api.arn
}

resource "aws_iam_role_policy" "eligibility_feed_lambda_execution" {
  name   = "massgov-pfml-${var.environment_name}-eligibility_feed_lambda_execution_role"
  role   = aws_iam_role.eligibility_feed_lambda_role.id
  policy = data.aws_iam_policy_document.iam_policy_eligibility_feed_lambda_execution.json
}

data "aws_iam_policy_document" "iam_policy_eligibility_feed_lambda_execution" {
  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParametersByPath"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
    ]
  }
}


data "aws_iam_policy_document" "iam_policy_access_ssm" {
  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParametersByPath"
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
    ]
  }
}

resource "aws_iam_policy" "access_ssm_policy" {
  name   = "${local.app_name}-${var.environment_name}-access_ssm_policy"
  policy = data.aws_iam_policy_document.iam_policy_access_ssm.json
}

# Normally this would be rolled into `eligibility_feed_lambda_execution` above,
# but we may not always have a value for `fineos_aws_iam_role_arn` and a policy
# has to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "eligibility_feed_lambda_execution_fineos" {
  count = var.fineos_aws_iam_role_arn == null ? 0 : 1

  name   = "massgov-pfml-${var.environment_name}-eligibility_feed_lambda_execution_role_fineos"
  role   = aws_iam_role.eligibility_feed_lambda_role.id
  policy = data.aws_iam_policy_document.iam_policy_eligibility_feed_lambda_execution_fineos[0].json
}

data "aws_iam_policy_document" "iam_policy_eligibility_feed_lambda_execution_fineos" {
  count = var.fineos_aws_iam_role_arn == null ? 0 : 1

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

# ----------------------------------------------------------------------------------------------------------------------
# IAM stuff for RDS
# ----------------------------------------------------------------------------------------------------------------------

# IAM role for allowing RDS instance to send monitoring insights to cloudwatch.
# Pulled from https://github.com/terraform-aws-modules/terraform-aws-rds/
#
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name_prefix        = "rds-enhanced-monitoring-${local.shorthand_env_name}-"
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

# ----------------------------------------------------------------------------------------------------------------------
# IAM stuff for S3
# ----------------------------------------------------------------------------------------------------------------------

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
      type        = "AWS"
      identifiers = var.environment_name == "prod" ? module.constants.prod_admin_roles : module.constants.nonprod_admin_roles
    }
  }

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

# IAM policy that defines get access rights to the S3 feature gate buckets
data "aws_iam_policy_document" "feature_gate" {

  statement {

    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-feature-gate",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-feature-gate/*"
    ]

  }
}
