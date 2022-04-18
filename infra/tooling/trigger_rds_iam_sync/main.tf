locals {
  name = "trigger_rds_iam_sync"
}
data "archive_file" "trigger_rds_iam_sync" {
  type        = "zip"
  output_path = "lambda_functions/${local.name}/${local.name}.zip"
  source_file = "lambda_functions/${local.name}/${local.name}.py"
}
resource "aws_lambda_function" "trigger_rds_iam_sync" {
  description      = "Trigger RDS IAM Sync GitHub Action"
  filename         = data.archive_file.trigger_rds_iam_sync.output_path
  source_code_hash = data.archive_file.trigger_rds_iam_sync.output_base64sha256
  function_name    = "${var.prefix}${local.name}"
  handler          = "${local.name}.handler"
  role             = aws_iam_role.trigger_rds_iam_sync.arn
  runtime          = "python3.8"
  memory_size      = 128
  publish          = "false"
  timeout          = 10
  layers           = [aws_lambda_layer_version.lambda_layer.arn]
}

resource "aws_lambda_layer_version" "lambda_layer" {
  filename            = "lambda_layers/github_layer.zip"
  layer_name          = "GitHub_Library"
  compatible_runtimes = ["python3.8"]
}

resource "aws_cloudwatch_event_rule" "trigger_rds_iam_sync" {
  name          = "${var.prefix}${local.name}"
  description   = "Invoke Lambda Function: ${var.prefix}${local.name}"
  event_pattern = <<EOF
{
  "source": ["aws.rds"],
  "detail-type": ["RDS DB Snapshot Event", "RDS DB Cluster Snapshot Event"],
  "detail": {
    "EventCategories": ["creation"],
    "SourceType": ["SNAPSHOT"],
    "SourceArn": ["${var.rds_cluster_arn}"],
    "Message": ["Automated snapshot created"]
  }
}
EOF
}

resource "aws_cloudwatch_event_target" "trigger_rds_iam_sync" {
  rule      = aws_cloudwatch_event_rule.trigger_rds_iam_sync.name
  target_id = "${var.prefix}${local.name}"
  arn       = aws_lambda_function.trigger_rds_iam_sync.arn
}

resource "aws_lambda_permission" "trigger_rds_iam_sync" {
  statement_id  = "invoke_${var.prefix}${local.name}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_rds_iam_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_rds_iam_sync.arn
}


