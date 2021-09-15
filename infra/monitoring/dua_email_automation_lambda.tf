# Lambda assume role policy 
data "aws_iam_policy_document" "dua_email_automation_lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Lambda ecs permissions policy
data "aws_iam_policy_document" "dua_email_automation_inline_policy" {
  statement {
    actions = [
      "s3:ListBucket",
      "s3:GetObject"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]
    resources = ["arn:aws:ses:us-east-1:498823821309:identity/PFML_DoNotReply@eol.mass.gov"]
  }
}

# IAM Role for lambda
resource "aws_iam_role" "dua_email_automation_lambda_role" {
  name               = "mass-pfml-dua-email-automation-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.dua_email_automation_lambda_assume_role.json

  inline_policy {
    name   = "dua-email-automation"
    policy = data.aws_iam_policy_document.dua_email_automation_inline_policy.json
  }
}

# Allow lambda to create logs
resource "aws_iam_role_policy_attachment" "dua_email_automation_lambda_basic_executor" {
  role = aws_iam_role.dua_email_automation_lambda_role.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "dua_email_automation" {
  description      = "Fetches daily DUA_DFML file and sends it to mailing list"
  filename         = data.archive_file.dua_email_automation_lambda_code.output_path
  source_code_hash = data.archive_file.dua_email_automation_lambda_code.output_base64sha256
  function_name    = "massgov-pfml-dua-email-automation"
  handler          = "dua_email_automation_lambda.lambda_handler"
  role             = aws_iam_role.dua_email_automation_lambda_role.arn
  runtime          = "python3.8"
  publish          = "false"
  timeout          = 60 # 1 minute

  tags = module.constants.common_tags
}

data "archive_file" "dua_email_automation_lambda_code" {
  type        = "zip"
  output_path = "${path.module}/.zip/dua_email_automation_lambda.zip"

  source {
    filename = "dua_email_automation_lambda.py"
    content  = file("${path.module}/dua_email_automation_lambda.py")
  }
}
