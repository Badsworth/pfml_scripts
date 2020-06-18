#
# Lambda@Edge configuration for modifying Cloudfront response headers
#

data "archive_file" "cloudfront_handler" {
  type        = "zip"
  source_file = "${path.module}/cloudfront-handler.js"
  output_path = "${path.module}/.zip/cloudfront-handler.zip"
}

resource "aws_lambda_function" "cloudfront_handler" {
  description      = "Customizes Cloudfront requests and responses"
  filename         = "${path.module}/.zip/cloudfront-handler.zip"
  function_name    = "${local.app_name}-${var.environment_name}-cloudfront_handler"
  role             = aws_iam_role.lambda_basic_executor.arn
  handler          = "cloudfront-handler.handler"
  source_code_hash = data.archive_file.cloudfront_handler.output_base64sha256
  runtime          = "nodejs12.x"
  publish          = true
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cloudfront_handler.function_name
  principal     = "events.amazonaws.com"
}
