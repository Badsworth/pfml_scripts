module "constants" {
  source = "../../constants"
}

locals {
  auditors = jsondecode(file("auditors.json"))
}

data "archive_file" "audit" {
  for_each    = local.auditors
  type        = "zip"
  source_dir  = "lambda_functions/audit_${each.key}"
  output_path = "lambda_functions/audit_${each.key}/audit_${each.key}.zip"
  excludes    = ["audit_${each.key}.zip"]
}

resource "aws_dynamodb_table" "inventory" {
  for_each     = local.auditors
  name         = "${var.prefix}${each.key}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ResourceName"

  attribute {
    name = "ResourceName"
    type = "S"
  }

  tags = merge({ "Name" : "${var.prefix}${each.key}" }, var.tags)
}

resource "aws_lambda_function" "audit" {
  for_each         = local.auditors
  description      = each.key
  filename         = data.archive_file.audit[each.key].output_path
  source_code_hash = data.archive_file.audit[each.key].output_base64sha256
  function_name    = "${var.prefix}${each.key}"
  handler          = "${var.prefix}${each.key}.handler"
  role             = aws_iam_role.audit[each.key].arn
  runtime          = "python3.9"

  environment {
    variables = {
      "REGION"               = var.aws_region,
      "INVENTORY_TABLE_NAME" = aws_dynamodb_table.inventory[each.key].name,
    }
  }

  tags = merge({ "Name" : "${var.prefix}${each.key}" }, var.tags)
}

resource "aws_cloudwatch_event_rule" "audit" {
  for_each            = local.auditors
  name                = "${var.prefix}${each.key}"
  description         = "Invoke Lambda Function: ${var.prefix}${each.key}"
  schedule_expression = var.schedule
}

resource "aws_cloudwatch_event_target" "audit" {
  for_each  = local.auditors
  rule      = aws_cloudwatch_event_rule.audit[each.key].name
  target_id = "${var.prefix}${each.key}"
  arn       = aws_lambda_function.audit[each.key].arn
}

resource "aws_lambda_permission" "audit" {
  for_each      = local.auditors
  statement_id  = "invoke_${var.prefix}${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.audit[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.audit[each.key].arn
}
