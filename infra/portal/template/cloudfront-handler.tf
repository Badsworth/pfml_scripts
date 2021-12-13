#
# Lambda@Edge configuration for modifying Cloudfront response headers
# TODO (PORTAL-1284): Remove these Terraform resources
#

data "archive_file" "cloudfront_handler" {
  type        = "zip"
  output_path = "${path.module}/.zip/cloudfront-handler.zip"
  # Do not delete this .js file as part of PORTAL-1284 since
  # it's still depended upon by the Cloudfront Function:
  source_file = "${path.module}/cloudfront-handler.js"
}

resource "aws_lambda_function" "cloudfront_handler" {
  description      = "Customizes Cloudfront requests and responses"
  filename         = "${path.module}/.zip/cloudfront-handler.zip"
  function_name    = "${local.app_name}-${var.environment_name}-cloudfront_handler"
  role             = aws_iam_role.lambda_basic_executor.arn
  handler          = "cloudfront-handler.handler"
  source_code_hash = data.archive_file.cloudfront_handler.output_base64sha256
  runtime          = "nodejs12.x"

  # Cloudfront lambda function associations need to use published, static version
  publish = true
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
