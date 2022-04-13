data "aws_ssm_parameter" "trigger_rds_iam_sync_token" {
  name = "/service/pfml-api/github/trigger-rds-iam-sync-token"
}
resource "aws_iam_policy_document" "trigger_rds_iam_sync_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "trigger_rds_iam_sync" {
  name               = "rds-iam-refresh-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.trigger_rds_iam_sync_trust_policy.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
  inline_policy {
    name = "lambda-get-parameter"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action   = "ssm:GetParameter"
          Effect   = "Allow"
          Resource = data.aws_ssm_parameter.trigger_rds_iam_sync_token.arn
        },
      ]
    })
  }
}
