#
# Terraform configuration for IAM roles.
#

# Lambda execution role. This role is used by Lambda to access AWS services and resources
#
# See: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"

      identifiers = [
        "lambda.amazonaws.com", "edgelambda.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role" "lambda_basic_executor" {
  name               = "${local.app_name}-${var.environment_name}-lambda-basic-executor"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_executor" {
  role = aws_iam_role.lambda_basic_executor.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

#--------------------------------------------------------------------------------------------------
# Cognito MFA
#--------------------------------------------------------------------------------------------------

resource "aws_iam_role" "cognito_mfa_sms_messages" {
  name               = "massgov-${local.app_name}-portal-${local.shorthand_env_name}-cognito-mfa-sms-messages"
  assume_role_policy = data.aws_iam_policy_document.cognito_mfa_sms_messages_assume_role.json
}

resource "aws_iam_policy" "cognito_mfa_sms_messages" {
  name   = "massgov-${local.app_name}-portal-${local.shorthand_env_name}-cognito-mfa-sms-messages"
  policy = data.aws_iam_policy_document.cognito_mfa_sms_messages.json
}

resource "aws_iam_role_policy_attachment" "cognito_mfa_sms_messages" {
  role       = aws_iam_role.cognito_mfa_sms_messages.name
  policy_arn = aws_iam_policy.cognito_mfa_sms_messages.arn
}

data "aws_iam_policy_document" "cognito_mfa_sms_messages_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["cognito-idp.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = ["massgov-${local.app_name}-portal-${local.shorthand_env_name}-mfa-sms"]
    }
  }
}

data "aws_iam_policy_document" "cognito_mfa_sms_messages" {
  statement {
    actions   = ["sns:publish"]
    resources = ["*"]
  }
}