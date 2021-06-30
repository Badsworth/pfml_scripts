#
# Terraform configuration for Lambda functions.
#

locals {
  # This ARN describes a 3rd-party lambda layer sourced directly from New Relic. It is not managed with Terraform.
  # This layer causes telemetry data to be generated and logged to CloudWatch as a side effect of lambda invocation.
  # Lambda layers are also available for runtimes other than Python 3.8: see https://nr-layers.iopipe.com/.
  newrelic_log_ingestion_layer = "arn:aws:lambda:us-east-1:451483290750:layer:NewRelicPython38:16"
}

data "aws_s3_bucket" "lambda_build" {
  bucket = "massgov-pfml-api-lambda-builds"
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_lambda_alias" "cognito_pre_signup__latest" {
  count            = var.cognito_enable_provisioned_concurrency ? 1 : 0
  name             = "most_recent"
  description      = "Most recent version of ${aws_lambda_function.cognito_pre_signup.function_name}"
  function_name    = aws_lambda_function.cognito_pre_signup.function_name
  function_version = aws_lambda_function.cognito_pre_signup.version
}

resource "aws_lambda_function" "cognito_pre_signup" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = "cognito-pre-signup/${var.cognito_pre_signup_lambda_artifact_s3_key}"

  # This function is connected to Cognito in the Portal Terraform configs via
  # this name, any changes to the function name should be done by deploying a
  # new Lambda function with the updated name, updating the Portal config to
  # point to new Lambda, then drop the old Lambda. Otherwise downtime is
  # required/User creation is broken.
  function_name = "massgov-pfml-${var.environment_name}-cognito_pre_signup"
  handler       = "newrelic_lambda_wrapper.handler" # the entrypoint of the newrelic instrumentation layer
  runtime       = var.runtime_py

  # New version publishes are needed for provisioned concurrency, but only in envs where that feature is enabled.
  # TODO (API-910): Remove obsolete lambda versions on a regular schedule so we don't run out of storage space.
  publish = var.cognito_enable_provisioned_concurrency

  # Cognito will only wait 5 seconds, so match that timeout here for
  # consistency.
  timeout = 5

  role   = aws_iam_role.cognito_pre_signup_lambda_role.arn
  layers = [local.newrelic_log_ingestion_layer]

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
      ENVIRONMENT                           = var.environment_name
      DB_HOST                               = aws_db_instance.default.address
      DB_NAME                               = aws_db_instance.default.name
      DB_USERNAME                           = "pfml_api"
      NEW_RELIC_ACCOUNT_ID                  = local.newrelic_account_id
      NEW_RELIC_TRUSTED_ACCOUNT_KEY         = local.newrelic_trusted_account_key
      NEW_RELIC_LAMBDA_HANDLER              = "handler.handler" # the actual lambda entrypoint
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# TODO: Temporary addition to avoid portal downtime. Remove after API-544 has been deployed to both API and Portal prod.
resource "aws_lambda_permission" "allow_cognito_pre_signup" {
  statement_id  = "AllowDirectExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_pre_signup.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
}

resource "aws_lambda_permission" "allow_cognito_pre_signup_alias" {
  count         = var.cognito_enable_provisioned_concurrency ? 1 : 0
  statement_id  = "AllowAliasExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_pre_signup.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
  qualifier     = aws_lambda_alias.cognito_pre_signup__latest[0].name
}

# Keep five instances of this lambda 'hot' at all times. Scales down to one instance outside of business hours EST.
resource "aws_lambda_provisioned_concurrency_config" "cognito_pre_signup_concurrency_settings" {
  count                             = var.cognito_enable_provisioned_concurrency ? 1 : 0
  qualifier                         = aws_lambda_alias.cognito_pre_signup__latest[0].name
  function_name                     = aws_lambda_alias.cognito_pre_signup__latest[0].function_name
  provisioned_concurrent_executions = var.cognito_provisioned_concurrency_level_max

  # An AWS autoscaling policy will alter this value, so ignore changes to it that come from Terraform.
  lifecycle {
    ignore_changes = [provisioned_concurrent_executions]
  }
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_lambda_alias" "cognito_post_confirmation__latest" {
  count            = var.cognito_enable_provisioned_concurrency ? 1 : 0
  name             = "most_recent"
  description      = "Most recent version of ${aws_lambda_function.cognito_post_confirmation.function_name}"
  function_name    = aws_lambda_function.cognito_post_confirmation.function_name
  function_version = aws_lambda_function.cognito_post_confirmation.version
}

resource "aws_lambda_function" "cognito_post_confirmation" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = "cognito-post-confirmation/${var.cognito_post_confirmation_lambda_artifact_s3_key}"

  # This function is connected to Cognito in the Portal Terraform configs via
  # this name, any changes to the function name should be done by deploying a
  # new Lambda function with the updated name, updating the Portal config to
  # point to new Lambda, then drop the old Lambda. Otherwise downtime is
  # required/User creation is broken.
  function_name = "massgov-pfml-${var.environment_name}-cognito_post_confirmation"
  handler       = "newrelic_lambda_wrapper.handler" # the entrypoint of the newrelic instrumentation layer
  runtime       = var.runtime_py

  # New version publishes are needed for provisioned concurrency, but only in envs where that feature is enabled.
  # TODO (API-910): Remove obsolete lambda versions on a regular schedule so we don't run out of storage space.
  publish = var.cognito_enable_provisioned_concurrency

  # Cognito will only wait 5 seconds, so match that timeout here for
  # consistency.
  timeout = 5

  role   = aws_iam_role.cognito_post_confirmation_lambda_role.arn
  layers = [local.newrelic_log_ingestion_layer]

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
      ENVIRONMENT                                 = var.environment_name
      DB_HOST                                     = aws_db_instance.default.address
      DB_NAME                                     = aws_db_instance.default.name
      DB_USERNAME                                 = "pfml_api"
      NEW_RELIC_ACCOUNT_ID                        = local.newrelic_account_id
      NEW_RELIC_TRUSTED_ACCOUNT_KEY               = local.newrelic_trusted_account_key
      NEW_RELIC_LAMBDA_HANDLER                    = "handler.handler" # the actual lambda entrypoint
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED       = true
      FINEOS_CLIENT_CUSTOMER_API_URL              = var.fineos_client_customer_api_url
      FINEOS_CLIENT_GROUP_CLIENT_API_URL          = var.fineos_client_group_client_api_url
      FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL  = var.fineos_client_integration_services_api_url
      FINEOS_CLIENT_WSCOMPOSER_API_URL            = var.fineos_client_wscomposer_api_url
      FINEOS_CLIENT_OAUTH2_URL                    = var.fineos_client_oauth2_url
      FINEOS_CLIENT_OAUTH2_CLIENT_ID              = var.fineos_client_oauth2_client_id
      FINEOS_CLIENT_OAUTH2_CLIENT_SECRET_SSM_PATH = "/service/${local.app_name}/${var.environment_name}/fineos_oauth2_client_secret"
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# TODO: Temporary addition to avoid portal downtime. Remove after API-544 has been deployed to both API and Portal prod.
resource "aws_lambda_permission" "allow_cognito_post_confirmation" {
  statement_id  = "AllowDirectExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_post_confirmation.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
}

resource "aws_lambda_permission" "allow_cognito_post_confirmation_alias" {
  count         = var.cognito_enable_provisioned_concurrency ? 1 : 0
  statement_id  = "AllowAliasExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_post_confirmation.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
  qualifier     = aws_lambda_alias.cognito_post_confirmation__latest[0].name
}

# Keep five instances of this lambda 'hot' at all times. Scales down to one instance outside of business hours EST.
resource "aws_lambda_provisioned_concurrency_config" "cognito_post_confirmation_concurrency_settings" {
  count                             = var.cognito_enable_provisioned_concurrency ? 1 : 0
  qualifier                         = aws_lambda_alias.cognito_post_confirmation__latest[0].name
  function_name                     = aws_lambda_alias.cognito_post_confirmation__latest[0].function_name
  provisioned_concurrent_executions = var.cognito_provisioned_concurrency_level_max

  # An AWS autoscaling policy will alter this value, so ignore changes to it that come from Terraform.
  lifecycle {
    ignore_changes = [provisioned_concurrent_executions]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
