
data "archive_file" "iam_refresh" {
  type        = "zip"
  output_path = "./.zip/trigger_rds_iam_sync.zip"

  source {
    filename = ".py"
    content  = file("../lambda_functions/trigger_rds_iam_sync.py")
  }
}
resource "aws_lambda_function" "iam_refresh" {
  description      = "Trigger RDS IAM Auto Refresh GitHub Action"
  filename         = data.archive_file.iam_refresh.output_path
  source_code_hash = data.archive_file.iam_refresh.output_base64sha256
  function_name    = "rds-iam-refresh"
  handler          = "lambda_functions.lambda_handler"
  role             = aws_iam_role.iam_refresh.arn
  runtime          = "python3.8"
  memory_size      = 128
  publish          = "false"
  timeout          = 10

}

