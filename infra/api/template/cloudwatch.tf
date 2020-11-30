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


resource "aws_cloudwatch_event_target" "trigger_formstack_import_lambda_daily_at_11_pm" {
  rule      = aws_cloudwatch_event_rule.formstack_lambda_daily_11pm_et.name
  arn       = aws_lambda_function.formstack_import.arn
  target_id = "formstack_import_${var.environment_name}_lambda_event_target"
  input     = "{\"is_daily_lambda\":true}"
}

resource "aws_cloudwatch_event_rule" "formstack_lambda_daily_11pm_et" {
  name        = "${var.environment_name}-formstack-lambda-daily-at-11-pm"
  description = "Fires the ${var.environment_name} Formstack Import lambda daily at 11pm US EDT/3am UTC"
  # The time of day can only be specified in UTC and will need to be updated when daylight savings changes occur, if the 2300 US ET is desired to be consistent.
  schedule_expression = "cron(0 03 * * ? *)"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_formstack_import" {
  statement_id  = "Allow${title(var.environment_name)}ExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.formstack_import.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.formstack_lambda_daily_11pm_et.arn
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

resource "aws_lambda_permission" "nr_lambda_permission_cognito_presignup" {
  statement_id  = "NRLambdaPermission_CognitoPreSign_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.lambda_cognito_presignup.arn}:*"
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

resource "aws_lambda_permission" "nr_lambda_permission_cognito_postconf" {
  statement_id  = "NRLambdaPermission_CognitoPostConf_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.lambda_cognito_postconf.arn}:*"
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

resource "aws_cloudwatch_log_group" "lambda_formstack_import" {
  name = "/aws/lambda/${aws_lambda_function.formstack_import.function_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_formstack_import" {
  name            = "nr_lambda_formstack_import"
  log_group_name  = aws_cloudwatch_log_group.lambda_formstack_import.name
  filter_pattern  = ""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_formstack_import" {
  statement_id  = "NRLambdaPermission_FormstackImport_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.lambda_formstack_import.arn}:*"
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

resource "aws_cloudwatch_log_group" "lambda_eligibility_feed" {
  name = "/aws/lambda/${aws_lambda_function.eligibility_feed.function_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_eligibility_feed" {
  name            = "nr_lambda_eligibility_feed"
  log_group_name  = aws_cloudwatch_log_group.lambda_eligibility_feed.name
  filter_pattern  = ""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_eligibility_feed" {
  statement_id  = "NRLambdaPermission_EligibilityFeed_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.lambda_eligibility_feed.arn}:*"
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
