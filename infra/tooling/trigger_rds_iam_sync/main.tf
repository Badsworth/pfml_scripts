
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
  function_name    = "massgov_pfml_trigger_rds_iam_sync"
  handler          = "trigger_rds_iam_sync.handler"
  role             = aws_iam_role.trigger_rds_iam_sync.arn
  runtime          = "python3.8"
  memory_size      = 128
  publish          = "false"
  timeout          = 10

}

