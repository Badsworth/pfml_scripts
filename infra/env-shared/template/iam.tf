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

# Allow pfmldata endpoint under API gateway to use S3 operations at specified resource locations. 

data "aws_iam_policy_document" "pfmldata_executor_policy_document" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:ListBucket",
      "s3:GetObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions/dia/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions/dua/*",
    ]
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
