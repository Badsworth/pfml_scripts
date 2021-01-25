locals {
  newrelic_aws_account_id = "754728514883"
  newrelic_account_id     = "2837112"
}

resource "aws_iam_role" "newrelic" {
  name               = "NewRelicInfrastructure-Integrations"
  assume_role_policy = data.aws_iam_policy_document.newrelic_assume_role_policy_document.json
}

data "aws_iam_policy_document" "newrelic_assume_role_policy_document" {
  statement {
    sid     = "AllowAssumeRoleForNewrelic"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = [local.newrelic_aws_account_id]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [local.newrelic_account_id]
    }
  }
}

data "aws_iam_policy" "read_only" {
  arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "newrelic_readonly_policy_attachment" {
  role       = aws_iam_role.newrelic.id
  policy_arn = data.aws_iam_policy.read_only.arn
}

# Allows the newrelic log ingestion lambda to retrieve its telemetry from any and all CloudWatch log groups.
resource "aws_lambda_permission" "nr_lambda_permission_generic" {
  statement_id  = "NRLambdaPermission_AnyLogGroup"
  action        = "lambda:InvokeFunction"
  principal     = "logs.us-east-1.amazonaws.com"
  function_name = module.constants.newrelic_log_ingestion_arn
  source_arn    = "arn:aws:logs:us-east-1:498823821309:log-group:*:*"
}
