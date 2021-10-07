#
# Lambda@Edge configuration for modifying Cloudfront response headers
#

data "archive_file" "cloudfront_handler" {
  type        = "zip"
  source_file = "${path.module}/cloudfront-handler.js"
  output_path = "${path.module}/.zip/cloudfront-handler.zip"
}
