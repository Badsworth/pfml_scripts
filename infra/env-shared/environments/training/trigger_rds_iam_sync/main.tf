
data "archive_file" "iam_refresh" {
  type        = "zip"
  output_path = "../lambda_functions/trigger_rds_iam_sync/trigger_rds_iam_sync.zip"
  source_dir = "../lambda_functions/trigger_rds_iam_sync"
  excludes = ["../lambda_functions/trigger_rds_iam_sync/trigger_rds_iam_sync.zip"]
}
resource "aws_lambda_function" "iam_refresh" {
  description      = "Trigger RDS IAM Auto Refresh GitHub Action"
  filename         = data.archive_file.iam_refresh.output_path
  source_code_hash = data.archive_file.iam_refresh.output_base64sha256
  function_name    = "massgov_pfml_trigger_rds_iam_sync"
  handler          = "trigger_rds_iam_sync.handler"
  role             = aws_iam_role.iam_refresh.arn
  runtime          = "python3.8"
  memory_size      = 128
  publish          = "false"
  timeout          = 10

}

