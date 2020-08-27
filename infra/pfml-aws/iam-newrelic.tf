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
