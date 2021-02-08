# Kinesis Data Firehose (KDF)

data "aws_ssm_parameter" "newrelic-insert-api-key" {
  name = "/admin/pfml-api/newrelic-insert-api-key"
}

resource "aws_kinesis_firehose_delivery_stream" "aws_waf" {
  name        = "aws-waf-logs-${var.environment_name}-firewall-to-newrelic"
  destination = "http_endpoint"

  s3_configuration {
    role_arn           = aws_iam_role.kinesis_aws_waf_role.arn
    bucket_arn         = aws_s3_bucket.kinesis_dead_letter_drop.arn
    buffer_size        = 5
    buffer_interval    = 300
    compression_format = "GZIP"
  }

  http_endpoint_configuration {
    url                = "https://aws-api.newrelic.com/firehose/v1"
    name               = "New Relic"
    access_key         = data.aws_ssm_parameter.newrelic-insert-api-key.value
    buffering_size     = 1
    buffering_interval = 60
    role_arn           = aws_iam_role.kinesis_aws_waf_role.arn
    s3_backup_mode     = "FailedDataOnly"

    request_configuration {
      content_encoding = "GZIP"
    }
  }
}

# Kinesis Data Firehose (KDF) data sources. Only one arn per resource is 
# currently supported. 

#------------------------------------------------------------------------------#
#              AWS WAF Regional Rate Limit ACL (API Gateway)                   #
#------------------------------------------------------------------------------#
resource "aws_wafv2_web_acl_logging_configuration" "regional_rate_based_acl" {
  count                   = var.enable_regional_rate_based_acl ? 1 : 0
  log_destination_configs = [aws_kinesis_firehose_delivery_stream.aws_waf.arn]
  resource_arn            = aws_wafv2_web_acl.regional_rate_based_acl[0].arn
}
