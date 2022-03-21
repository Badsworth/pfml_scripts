#
# Lambda filter for NewRelic Kinesis Firehose.
#
resource "aws_lambda_function" "kinesis_filter" {
  description      = var.function_description
  filename         = data.archive_file.lambda_filter_function.output_path
  source_code_hash = data.archive_file.lambda_filter_function.output_base64sha256
  function_name    = "massgov-pfml-${var.function_name}"
  handler          = "${var.function_name}.lambda_handler"
  role             = aws_iam_role.lambda_kinesis_executor.arn
  runtime          = "python3.9"
  memory_size      = "256"
  publish          = "false"
  timeout          = "240"

  tags = module.constants.common_tags
}

data "archive_file" "lambda_filter_function" {
  type        = "zip"
  source_file = "${var.source_file_path}/${var.function_name}.py"
  output_path = "${var.source_file_path}/.zip/${var.function_name}.zip"
}

#-------------------------------------------------------------------------------------
