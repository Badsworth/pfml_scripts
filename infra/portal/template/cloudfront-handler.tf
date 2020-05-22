#
# Lambda@Edge configuration for modifying Cloudfront response headers 
#

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/cloudfront-handler.js"
  output_path = "${path.module}/.zip/cloudfront-handler.zip"
}

resource "aws_lambda_function" "edge_headers" {
  filename         = "${path.module}/.zip/cloudfront-handler.zip"
  function_name    = "${local.app_name}-${var.environment_name}-edge_headers"
  role             = "${aws_iam_role.lambda_basic_executor.arn}"
  handler          = "cloudfront-handler.handler"
  source_code_hash = "${data.archive_file.lambda_zip.output_base64sha256}"
  runtime          = "nodejs10.x"
  publish          = true
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.edge_headers.function_name}"
  principal     = "events.amazonaws.com"
}
