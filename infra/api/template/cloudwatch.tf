# Cloudwatch log groups for streaming ECS application logs and telemetry from application lambdas.

locals {
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = module.constants.newrelic_log_ingestion_arn
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "service_logs" {
  name = "service/${local.app_name}-${var.environment_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "ecs_service_logging" {
  name            = "ecs_service_logs"
  log_group_name  = aws_cloudwatch_log_group.service_logs.name
  destination_arn = local.newrelic_log_ingestion_lambda
  # matches all log events
  filter_pattern = ""
}

resource "aws_lambda_permission" "ecs_permission_service_logging" {
  statement_id  = "NRLambdaPermission_ECSLogging_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.service_logs.arn}:*"
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda_cognito_presignup" {
  name = "/aws/lambda/${aws_lambda_function.cognito_pre_signup.function_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_cognito_presignup" {
  name            = "nr_lambda_cognito_presignup"
  log_group_name  = aws_cloudwatch_log_group.lambda_cognito_presignup.name
  filter_pattern  = ""
  destination_arn = local.newrelic_log_ingestion_lambda
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda_cognito_postconf" {
  name = "/aws/lambda/${aws_lambda_function.cognito_post_confirmation.function_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_cognito_postconf" {
  name            = "nr_lambda_cognito_postconf"
  log_group_name  = aws_cloudwatch_log_group.lambda_cognito_postconf.name
  filter_pattern  = ""
  destination_arn = local.newrelic_log_ingestion_lambda
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

