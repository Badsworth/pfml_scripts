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
  publish       = "false"

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

resource "aws_lambda_permission" "allow_cognito_pre_signup" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_pre_signup.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
}

# ----------------------------------------------------------------------------------------------------------------------

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
  publish       = "false"

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

resource "aws_lambda_permission" "allow_cognito_post_confirmation" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_post_confirmation.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_lambda_function" "formstack_import" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = "formstack-import/${var.formstack_import_lambda_build_s3_key}"

  function_name = "massgov-pfml-${var.environment_name}-formstack-import"
  handler       = "newrelic_lambda_wrapper.handler" # the entrypoint of the newrelic instrumentation layer
  runtime       = var.runtime_py
  publish       = "false"

  timeout = 900

  role = aws_iam_role.formstack_import_lambda_role.arn
  layers = [
    local.newrelic_log_ingestion_layer
  ]

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
      DB_HOST                               = aws_db_instance.default.address
      DB_NAME                               = aws_db_instance.default.name
      DB_USERNAME                           = "pfml_api"
      FORMSTACK_TOKEN_SSM_PATH              = "/service/${local.app_name}-formstack-import/formstack_token"
      FORMSTACK_OAUTH_INFO_SSM_PATH         = "/service/${local.app_name}-formstack-import/formstack_oauth_info"
      FORMSTACK_DATA_BUCKET_NAME            = "massgov-pfml-${var.environment_name}-formstack-data"
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

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_lambda_function" "eligibility_feed" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = "fineos-eligibility-feed-export/${var.fineos_eligibility_transfer_lambda_build_s3_key}"

  function_name = "massgov-pfml-${var.environment_name}-eligibility-feed"
  handler       = "newrelic_lambda_wrapper.handler" # the entrypoint of the newrelic instrumentation layer

  runtime = var.runtime_py
  publish = "false"

  memory_size = 1024
  timeout     = 900

  role   = aws_iam_role.eligibility_feed_lambda_role.arn
  layers = [local.newrelic_log_ingestion_layer]

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
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
      OUTPUT_DIRECTORY_PATH                       = var.fineos_eligibility_feed_output_directory_path
      FINEOS_AWS_IAM_ROLE_ARN                     = var.fineos_aws_iam_role_arn
      FINEOS_AWS_IAM_ROLE_EXTERNAL_ID             = var.fineos_aws_iam_role_external_id
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# ----------------------------------------------------------------------------------------------------------------------
