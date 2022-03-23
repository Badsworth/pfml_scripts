# Add Kinesis subscription to log groups
resource "aws_cloudwatch_log_subscription_filter" "kinesis" {
  for_each        = toset(var.cw_log_group_names)
  name            = "Kinesis_to_New_Relic"
  log_group_name  = each.key
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.kinesis_to_newrelic.arn
  role_arn        = aws_iam_role.cloudwatch_writes_to_kinesis.arn
}

# ----------------------------------------------------------------------------------------------------------------------
# Kinesis Firehose log group for errors deliverying to NewRelic
resource "aws_cloudwatch_log_group" "kinesis_service_logs" {
  name = "/aws/kinesisfirehose/${var.kinesis_firehose_name}"

  tags = module.constants.common_tags
}

# Log stream for NewRelic HTTP Endpoint
resource "aws_cloudwatch_log_stream" "kinesis_service_logs" {
  name           = "HttpEndpointDelivery"
  log_group_name = aws_cloudwatch_log_group.kinesis_service_logs.name
}

# ----------------------------------------------------------------------------------------------------------------------
# Set log retention for Lambda logs, these are informational only showing how many records processed
resource "aws_cloudwatch_log_group" "lambda_function" {
  name              = "/aws/lambda/${aws_lambda_function.kinesis_filter.function_name}"
  retention_in_days = 90
}