provider "aws" {
  region = "us-east-1"
}

data "aws_region" "current" {
}

data "aws_caller_identity" "current" {
}

module "constants" {
  source = "../../constants"
}

resource "aws_iam_role" "audit_lambda" {
  name               = "audit_lambda"
  assume_role_policy = data.aws_iam_policy_document.audit_lambda.json
}
resource "aws_iam_role_policy_attachment" "audit_lambda" {
  role       = aws_iam_role.audit_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "audit_lambda" {
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

resource "aws_dynamodb_table" "audit_lambda" {
  name         = "audit_lambda"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ResourceName"
  // range_key      = "FIXME"

  attribute {
    name = "ResourceName"
    type = "S"
  }

  // attribute {
  //   name = "FIXME"
  //   type = "S"
  // }

  tags = module.constants.common_tags

}


resource "aws_lambda_function" "audit_lambda" {
  description      = "Audit Lambda Functions"
  filename         = data.archive_file.audit_lambda.output_path
  source_code_hash = data.archive_file.audit_lambda.output_base64sha256
  function_name    = "massgov-pfml-audit-lambda"
  handler          = "audit_lambda.handler"
  role             = aws_iam_role.audit_lambda.arn
  runtime          = "python3.9"

  environment {
    variables = {
      "AWS_REGION"           = data.aws_region.current,
      "INVENTORY_TABLE_NAME" = aws_dynamodb_table.audit_lambda.name,
    }
  }

  tags = module.constants.common_tags
}

data "archive_file" "audit_lambda" {
  type        = "zip"
  source_file = "lambda_functions/audit_lambda/audit_lambda.py"
  output_path = "lambda_functions/audit_lambda/.zip/audit_lambda.zip"
}