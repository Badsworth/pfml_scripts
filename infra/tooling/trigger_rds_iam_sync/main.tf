
data "archive_file" "trigger_rds_iam_sync" {
  type        = "zip"
  output_path = "../lambda_functions/trigger_rds_iam_sync/trigger_rds_iam_sync.zip"
  source_dir = "../lambda_functions/trigger_rds_iam_sync"
  excludes = ["../lambda_functions/trigger_rds_iam_sync/trigger_rds_iam_sync.zip"]
}
resource "aws_lambda_function" "trigger_rds_iam_sync" {
  description      = "Trigger RDS IAM Sync GitHub Action"
  filename         = data.archive_file.trigger_rds_iam_sync.output_path
  source_code_hash = data.archive_file.trigger_rds_iam_sync.output_base64sha256
  function_name    = "${var.prefix}_trigger_rds_iam_sync"
  handler          = "trigger_rds_iam_sync.handler"
  role             = aws_iam_role.trigger_rds_iam_sync.arn
  runtime          = "python3.8"
  memory_size      = 128
  publish          = "false"
  timeout          = 10
}

resource "aws_cloudwatch_event_rule" "trigger_rds_iam_sync" {
  name                = "${var.prefix}_trigger_rds_iam_sync"
  description         = "Invoke Lambda Function: ${var.prefix}_trigger_rds_iam_sync"
  schedule_expression = ""
}

resource "aws_cloudwatch_event_target" "trigger_rds_iam_sync" {
  rule      = aws_cloudwatch_event_rule.trigger_rds_iam_sync.name
  target_id = "${var.prefix}_trigger_rds_iam_sync"
  arn       = aws_lambda_function.trigger_rds_iam_sync.arn
}

resource "aws_lambda_permission" "trigger_rds_iam_sync" {
  statement_id  = "invoke_${var.prefix}_trigger_rds_iam_sync"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_rds_iam_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_rds_iam_sync.arn
}


variable "secret_token_arn" {
  type = string
  description = "arn for ssm parameter that contains github token"
}

variable "prefix" {
  type = string
  description = "naming prefix"
}
