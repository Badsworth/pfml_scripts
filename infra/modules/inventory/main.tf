provider "aws" {}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

module "constants" {
  source = "../../constants"
}

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

  tags = merge({ "Name" = "massgov_pfml_audit_${each.key}" }, module.constants.common_tags)
}

data "archive_file" "audit" {
  for_each    = local.auditors
  type        = "zip"
  source_dir  = "lambda_functions/audit_${each.key}"
  output_path = "lambda_functions/audit_${each.key}/audit_${each.key}.zip"
  excludes    = ["audit_${each.key}.zip"]
}

resource "aws_lambda_function" "audit" {
  for_each         = local.auditors
  description      = each.key
  filename         = data.archive_file.audit[each.key].output_path
  source_code_hash = data.archive_file.audit[each.key].output_base64sha256
  function_name    = "massgov_pfml_audit_${each.key}"
  handler          = "massgov_pfml_audit_${each.key}.handler"
  role             = aws_iam_role.audit[each.key].arn
  runtime          = "python3.9"

  environment {
    variables = {
      "AWS_REGION"           = data.aws_region.current.name,
      "INVENTORY_TABLE_NAME" = aws_dynamodb_table.inventory[each.key].name,
    }
  }

  tags = merge({ "Name" = "massgov_pfml_audit_${each.key}" }, module.constants.common_tags)
}