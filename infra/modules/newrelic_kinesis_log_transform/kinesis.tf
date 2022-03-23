data "aws_ssm_parameter" "newrelic_insert_api_key" {
  name = "/admin/pfml-api/newrelic-insert-api-key"
}

#
# Kinesis Firehose to deliver sms cloudwatch logs to NewRelic with Lambda filter
#
resource "aws_kinesis_firehose_delivery_stream" "kinesis_to_newrelic" {
  name        = var.kinesis_firehose_name
  destination = "http_endpoint"

  # server_side_encryption {
  #   enabled     = true
  #   key_type    = "CUSTOMER_MANAGED_CMK"
  #   key_arn = aws_kms_key.main_kms_key.arn
  # }

  s3_configuration {
    bucket_arn         = aws_s3_bucket.kinesis_to_newrelic_dlq.arn
    role_arn           = aws_iam_role.kinesis_to_s3.arn
    buffer_size        = 1
    buffer_interval    = 60
    compression_format = "GZIP"
  }

  http_endpoint_configuration {
    url                = "https://aws-api.newrelic.com/firehose/v1"
    name               = "New Relic"
    access_key         = data.aws_ssm_parameter.newrelic_insert_api_key.value
    buffering_size     = 1
    buffering_interval = 60
    role_arn           = aws_iam_role.kinesis_to_s3.arn
    s3_backup_mode     = "FailedDataOnly"


    request_configuration {
      content_encoding = "GZIP"

      common_attributes {
        name  = "aws.logGroup"
        value = var.nr_log_group_name
      }
    }
    processing_configuration {
      enabled = "true"

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${aws_lambda_function.kinesis_filter.arn}:$LATEST"
        }

        parameters {
          parameter_name  = "BufferSizeInMBs"
          parameter_value = 1
        }

        parameters {
          parameter_name  = "BufferIntervalInSeconds"
          parameter_value = 61
        }
      }
    }

    cloudwatch_logging_options {
      enabled         = "true"
      log_group_name  = aws_cloudwatch_log_group.kinesis_service_logs.name
      log_stream_name = "HttpEndpointDelivery"
    }
  }
}
