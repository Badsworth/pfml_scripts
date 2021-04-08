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
