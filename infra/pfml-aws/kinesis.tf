data "aws_ssm_parameter" "newrelic_insert_api_key" {
  name = "/admin/pfml-api/newrelic-insert-api-key"
}

resource "aws_kinesis_firehose_delivery_stream" "ses_to_newrelic" {
  name        = "massgov-pfml-ses-newrelic"
  destination = "http_endpoint"
  tags        = module.constants.common_tags

  s3_configuration {
    bucket_arn         = aws_s3_bucket.ses_to_newrelic_dlq.arn
    role_arn           = aws_iam_role.firehose_to_newrelic_or_s3.arn
    buffer_size        = 1  # megabytes
    buffer_interval    = 60 # seconds
    compression_format = "GZIP"
  }

  http_endpoint_configuration {
    url                = "https://aws-api.newrelic.com/firehose/v1"
    name               = "New Relic"
    access_key         = data.aws_ssm_parameter.newrelic_insert_api_key.value
    buffering_size     = 1  # megabytes
    buffering_interval = 60 # seconds
    role_arn           = aws_iam_role.firehose_to_newrelic_or_s3.arn
    s3_backup_mode     = "FailedDataOnly"

    request_configuration {
      content_encoding = "GZIP"
    }
  }
}
