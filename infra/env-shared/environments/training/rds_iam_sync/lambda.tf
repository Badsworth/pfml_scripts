resource "aws_lambda_function" "iam_refresh" {
  description      = "RDS IAM AUTO REFRESH"
  filename         = data.archive_file.iam_refresh.output_path
  source_code_hash = data.archive_file.iam_refresh.output_base64sha256
  function_name    = "rds-iam-refresh"
  handler          = "lambda_functions.lambda_handler"
  role             = aws_iam_role.iam_refresh.arn
  runtime          = "python3.8"
  memory_size      = 128
  publish          = "false"
  timeout          = 10

  environment {
    variables = {
     RDS_IAM_REFRESH = data.aws_ssm_parameter.rds-iam-refresh.id
    }
  }
}

data "archive_file" "iam_refresh" {
  type        = "zip"
  output_path = "./.zip/aws_iam_refresh.zip"

  source {
    filename = ".py"
    content  = file("./aws_iam_refresh.py")
  }
}
