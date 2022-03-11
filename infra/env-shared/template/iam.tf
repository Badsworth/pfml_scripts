data "aws_iam_policy_document" "api_gateway_assume_role_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "executor" {
  name               = "pfml-${var.environment_name}-gateway-reports-executor"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume_role_policy.json
}

resource "aws_iam_role_policy" "reports_executor" {
  name   = "massgov-pfml-${var.environment_name}-reports-executor-role-policy"
  role   = aws_iam_role.executor.id
  policy = data.aws_iam_policy_document.reports_executor.json
}

data "aws_iam_policy_document" "reports_executor" {
  # Allow API gateway to read and delete files from dfml-reports.
  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.pfml_reports.arn}/dfml-reports/*",
    ]
  }

  # Allow API gateway to add files to dfml-responses.
  statement {
    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.pfml_reports.arn}/dfml-responses/*",
    ]
  }
}



# Allow Eventbridge to send ECS task change events to the ECS Task Events 
# cloudwatch log group
data "aws_iam_policy_document" "ecs-tasks-events-log-policy" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutLogEventsBatch",
    ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs.amazonaws.com", "events.amazonaws.com", "delivery.logs.amazonaws.com"]
    }

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks_events.arn}:*"
    ]
  }
}

resource "aws_cloudwatch_log_resource_policy" "ecs-tasks-events-log-publishing-policy" {
  policy_document = data.aws_iam_policy_document.ecs-tasks-events-log-policy.json
  policy_name     = "ecs-tasks-events-log-publishing-policy"
}

# Configures API gateway resources authorized for S3 operations 
# under the /files endpoint. 
resource "aws_iam_role" "files_executor_role" {
  for_each           = local.endpoints
  name               = "massgov-pfml-${var.environment_name}-${each.key}-executor"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume_role_policy.json
}

resource "aws_iam_role_policy" "files_executor_policy" {
  for_each = local.endpoints
  name     = "massgov-pfml-${var.environment_name}-${each.key}-policy"
  role     = aws_iam_role.files_executor_role[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "${each.value.bucket}*"
        Condition = {
          StringLike = {
            "s3:prefix" : "${each.value.object_prefix}*"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "s3:Put*",
          "s3:List*",
          "s3:Get*",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload"
        ]
        Resource = "${each.value.bucket}/${each.value.object_prefix}*"
      }
    ]
  })
}

# Allow pfmldata endpoint under API gateway to use S3 operations at specified resource locations. 
data "aws_iam_policy_document" "pfmldata_executor_policy_document" {
  dynamic "statement" {
    for_each = local.pfmldata_bucket_resources
    content {
      actions = [
        "s3:ListBucket"
      ]

      resources = [statement.value.bucket_arn]
      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values = [
          for r in statement.value.resource_prefixes : r
        ]
      }
      effect = "Allow"
    }
  }
  statement {
    sid = "AllowS3ReadWriteDeleteOnBucket"
    actions = [
      "s3:Put*",
      "s3:List*",
      "s3:Get*",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = local.pfmldata_bucket_resource_prefixes
  }
}

resource "aws_iam_role" "pfmldata_executor_role" {
  name               = "massgov-pfml-${var.environment_name}-data-api-gateway-executor"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume_role_policy.json
}

resource "aws_iam_role_policy" "pfmldata_executor_policy" {
  name   = "massgov-pfml-${var.environment_name}-data-executor-role-policy"
  role   = aws_iam_role.pfmldata_executor_role.id
  policy = data.aws_iam_policy_document.pfmldata_executor_policy_document.json
}


data "aws_iam_policy_document" "qlikdata_executor_policy_document" {
  # Allow API gateway to read and delete files from dfml-qlikdownloads.
  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.pfml_reports.arn}/dfml-qlikdownloads",
      "${aws_s3_bucket.pfml_reports.arn}/dfml-qlikdownloads/*"
    ]
  }

  # Allow API gateway to add files to dfml-qlikuploads.
  statement {
    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.pfml_reports.arn}/dfml-qlikuploads",
      "${aws_s3_bucket.pfml_reports.arn}/dfml-qlikuploads/*"
    ]
  }
}
resource "aws_iam_role" "qlikdata_executor_role" {
  name               = "massgov-pfml-${var.environment_name}-data-qlik-gateway-executor"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume_role_policy.json
}

resource "aws_iam_role_policy" "qlikdata_executor_policy" {
  name   = "massgov-pfml-${var.environment_name}-data-executor-role-policy"
  role   = aws_iam_role.qlikdata_executor_role.id
  policy = data.aws_iam_policy_document.qlikdata_executor_policy_document.json
}
