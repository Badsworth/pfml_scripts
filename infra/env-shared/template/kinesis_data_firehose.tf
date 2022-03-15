# Kinesis Data Firehose (KDF)

data "aws_ssm_parameter" "newrelic-insert-api-key" {
  name = "/admin/pfml-api/newrelic-insert-api-key"
}

resource "aws_kinesis_firehose_delivery_stream" "aws_waf" {
  name        = "aws-waf-logs-${var.environment_name}-kinesis-to-s3"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn            = aws_iam_role.kinesis_aws_waf_role.arn
    bucket_arn          = aws_s3_bucket.smx_kinesis_firewall_ingest.arn
    prefix              = "WAF_Logs/"
    error_output_prefix = "WAF_Logs_error/"
  }
}

# Kinesis Data Firehose (KDF) data sources. Only one arn per resource is
# currently supported.

#------------------------------------------------------------------------------#
#              AWS WAF Regional Rate Limit ACL (API Gateway)                   #
#------------------------------------------------------------------------------#
resource "aws_wafv2_web_acl_logging_configuration" "regional_api_acl" {
  count                   = var.enable_regional_api_acl ? 1 : 0
  log_destination_configs = [aws_kinesis_firehose_delivery_stream.aws_waf.arn]
  resource_arn            = aws_wafv2_web_acl.regional_api_acl.arn
}
