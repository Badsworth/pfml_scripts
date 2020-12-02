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
  publish          = false
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cloudfront_handler.function_name
  principal     = "events.amazonaws.com"
}

resource "aws_cloudwatch_log_group" "lambda_cloudfront_handler" {
  // Edge functions have a us-east-1 region prefix.
  name = "/aws/lambda/us-east-1.${aws_lambda_function.cloudfront_handler.function_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_cloudfront_handler" {
  name            = "nr_lambda_cloudfront_handler"
  log_group_name  = aws_cloudwatch_log_group.lambda_cloudfront_handler.name
  filter_pattern  = ""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_cloudfront_handler" {
  statement_id  = "NRLambdaPermission_CloudfrontHandler_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.lambda_cloudfront_handler.arn}:*"
}
