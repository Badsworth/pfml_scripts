resource "aws_lambda_function" "audit_lambda" {
  description      = "Audit Lambda Functions"
  filename         = data.archive_file.lambda_filter_function.output_path
  source_code_hash = data.archive_file.lambda_filter_function.output_base64sha256
  function_name    = "massgov-pfml-${var.function_name}"
  handler          = "${var.function_name}.handler"
  role             = aws_iam_role.audit_lambda.arn
  runtime          = "python3.9"

  tags = module.constants.common_tags
}

data "archive_file" "audit_lambda" {
  type        = "zip"
  source_file = "${var.source_file_path}/${var.function_name}.py"
  output_path = "${var.source_file_path}/.zip/${var.function_name}.zip"
}

#----