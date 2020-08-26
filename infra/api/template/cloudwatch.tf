# Cloudwatch log groups for streaming ECS application logs and telemetry from application lambdas.

locals {
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = "arn:aws:lambda:us-east-1:498823821309:function:newrelic-log-ingestion"
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "service_logs" {
  name = "service/${local.app_name}-${var.environment_name}"
}

resource "aws_cloudwatch_event_target" "trigger_dor_import_lambda_daily_at_11_pm" {
  rule      = aws_cloudwatch_event_rule.daily_11pm_et.name
  arn       = aws_lambda_function.dor_import.arn
  target_id = "dor_import_${var.environment_name}_lambda_event_target"
}

resource "aws_cloudwatch_event_rule" "daily_11pm_et" {
  name        = "daily-at-11-pm"
  description = "Fires once daily at 11pm US EDT/3am UTC"
  # The time of day can only be specified in UTC and will need to be updated when daylight savings changes occur, if the 2300 US ET is desired to be consistent.
  schedule_expression = "cron(0 03 * * ? *)"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_dor_import" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dor_import.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_11pm_et.arn
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_cognito_postconf" {
  name            = "nr_lambda_cognito_postconf"
  log_group_name  = "/aws/lambda/massgov-pfml-${var.environment_name}-cognito_post_confirmation"
  filter_pattern  = "?REPORT ?NR_LAMBDA_MONITORING ?\"Task timed out\""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_cognito_postconf" {
  statement_id  = "NRLambdaPermission_CognitoPostConf"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "arn:aws:logs:us-east-1:498823821309:log-group:/aws/lambda/massgov-pfml-${var.environment_name}-cognito_post_confirmation:*"
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_dor_import" {
  name            = "nr_lambda_dor_import"
  log_group_name  = "/aws/lambda/massgov-pfml-${var.environment_name}-dor-import"
  filter_pattern  = "?REPORT ?NR_LAMBDA_MONITORING ?\"Task timed out\""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_dor_import" {
  statement_id  = "NRLambdaPermission_DORImport"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "arn:aws:logs:us-east-1:498823821309:log-group:/aws/lambda/massgov-pfml-${var.environment_name}-dor-import:*"
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_eligibility_feed" {
  name            = "nr_lambda_eligibility_feed"
  log_group_name  = "/aws/lambda/massgov-pfml-${var.environment_name}-eligibility-feed"
  filter_pattern  = "?REPORT ?NR_LAMBDA_MONITORING ?\"Task timed out\""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_eligibility_feed" {
  statement_id  = "NRLambdaPermission_EligibilityFeed"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "arn:aws:logs:us-east-1:498823821309:log-group:/aws/lambda/massgov-pfml-${var.environment_name}-eligibility-feed:*"
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
