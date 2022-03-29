provider "aws" {}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  auditors = jsondecode(file("auditors.json"))
}

resource "aws_dynamodb_table" "inventory" {
  for_each     = local.auditors
  name         = "massgov_pfml_audit_${each.key}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ResourceName"

  attribute {
    name = "ResourceName"
    type = "S"
  }

  tags = {
    Name = "massgov_pfml_audit_${each.key}"
  }
}

data "aws_iam_policy_document" "auditor_iam_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type       = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "archive_file" "audit" {
  for_each    = local.auditors
  type        = "zip"
  source_dir  = "lambda_functions/audit_${each.key}"
  output_path = "lambda_functions/audit_lambda/audit_${each.key}.zip"
  excludes    = ["lambda_functions/audit_${each.key}/audit_${each.key}.zip"]
}

resource "aws_iam_role" "audit" {
  for_each           = local.auditors
  name               = "massgov_pfml_audit_${each.key}_role"
  assume_role_policy = data.aws_iam_policy_document.auditor_iam_policy.json
}

resource "aws_iam_role_policy_attachment" "audit" {
    for_each = local.auditors
  role       = aws_iam_role.auditor_iam_role[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "audit" {
  for_each         = local.auditors
  description      = each.key
  filename         = data.archive_file.auditor_function_package[each.key].output_path
  source_code_hash = data.archive_file.auditor_function_package[each.key].output_base64sha256
  function_name    = "massgov_pfml_audit_${each.key}"
  handler          = "massgov_pfml_audit_${each.key}.handler"
  role             = aws_iam_role.auditor_iam_role[each.key].arn
  runtime          = "python3.9"

  environment {
    variables = {
      "AWS_REGION"           = data.aws_region.current.name,
      "INVENTORY_TABLE_NAME" = aws_dynamodb_table.inventory[each.key].name,
    }
  }

  tags = {
    Name = "audit_${each.key}"
  }
}