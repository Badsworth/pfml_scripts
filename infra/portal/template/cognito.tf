locals {
  # This ARN describes a 3rd-party lambda layer sourced directly from New Relic. It is not managed with Terraform.
  # This layer causes telemetry data to be generated and logged to CloudWatch as a side effect of lambda invocation.
  newrelic_log_ingestion_layer = "arn:aws:lambda:us-east-1:451483290750:layer:NewRelicNodeJS12X:18"

  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = "arn:aws:lambda:us-east-1:498823821309:function:newrelic-log-ingestion"
}

resource "aws_cognito_user_pool" "claimants_pool" {
  name                     = "massgov-${local.app_name}-${var.environment_name}"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  email_configuration {
    # Use this SES email to send cognito emails. If we're not using SES for emails then use null
    source_arn            = var.ses_email_address == "" ? null : "arn:aws:ses:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:identity/${var.ses_email_address}"
    email_sending_account = var.ses_email_address == "" ? "COGNITO_DEFAULT" : "DEVELOPER"
    # Customize the name that users see in the "From" section of their inbox, so that it's clearer who the email is from
    from_email_address = var.ses_email_address == "" ? null : "\"Mass.gov\" <${var.ses_email_address}>"
  }

  sms_authentication_message = "Your authentication code is {####}. "

  lambda_config {
    custom_message    = aws_lambda_function.cognito_custom_message.arn
    post_confirmation = var.cognito_post_confirmation_lambda_arn
  }

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  username_configuration {
    case_sensitive = false
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    sms_message          = "Your Paid Family and Medical Leave verification code is {####}"
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = "true"
    required            = "true"

    string_attribute_constraints {
      max_length = 2048
      min_length = 0
    }
  }
}

resource "aws_cognito_user_pool_client" "massgov_pfml_client" {
  name         = "massgov-${local.app_name}-${var.environment_name}"
  user_pool_id = aws_cognito_user_pool.claimants_pool.id

  callback_urls                = concat(var.cognito_extra_redirect_urls, ["https://${aws_cloudfront_distribution.portal_web_distribution.domain_name}"])
  logout_urls                  = concat(var.cognito_extra_logout_urls, ["https://${aws_cloudfront_distribution.portal_web_distribution.domain_name}"])
  supported_identity_providers = ["COGNITO"]
  refresh_token_validity       = 1 # days

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["phone", "email", "openid", "profile", "aws.cognito.signin.user.admin"]

  # Avoid security issue where error messages indicate when a user doesn't exist
  prevent_user_existence_errors = "ENABLED"

  read_attributes  = ["email", "email_verified", "phone_number", "phone_number_verified", "updated_at"]
  write_attributes = ["email", "updated_at"]
}

resource "aws_cognito_user_pool_domain" "massgov_pfml_domain" {
  domain       = "massgov-${local.app_name}-${var.environment_name}"
  user_pool_id = aws_cognito_user_pool.claimants_pool.id
}

# Custom Cognito emails are sent by this Lambda function
resource "aws_lambda_function" "cognito_custom_message" {
  description      = "Customizes Cognito SMS and Email messages"
  filename         = data.archive_file.cognito_custom_message.output_path
  source_code_hash = data.archive_file.cognito_custom_message.output_base64sha256
  function_name    = "${local.app_name}-${var.environment_name}-cognito-custom-message"
  handler          = "newrelic-lambda-wrapper.handler" # the entrypoint of the newrelic instrumentation layer
  role             = aws_iam_role.lambda_basic_executor.arn
  layers           = [local.newrelic_log_ingestion_layer]
  runtime          = "nodejs12.x"

  environment {
    variables = {
      NEW_RELIC_ACCOUNT_ID                  = "2837112"        # PFML account
      NEW_RELIC_TRUSTED_ACCOUNT_KEY         = "1606654"        # EOLWD parent account
      NEW_RELIC_LAMBDA_HANDLER              = "lambda.handler" # the actual lambda entrypoint
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
    }
  }
}

data "archive_file" "cognito_custom_message" {
  type        = "zip"
  output_path = "${path.module}/.zip/cognito-message-handler.zip"

  source {
    filename = "lambda.js"
    content  = file("${path.module}/cognito-message-handler.js")
  }
}

# Allow the Lambda to be invoked by our user pool
resource "aws_lambda_permission" "allow_cognito_custom_message" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_custom_message.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.claimants_pool.arn
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_cognito_custom_msg" {
  name            = "nr_lambda_cognito_custom_msg"
  log_group_name  = "/aws/lambda/${aws_lambda_function.cognito_custom_message.function_name}"
  filter_pattern  = "?REPORT ?NR_LAMBDA_MONITORING ?\"Task timed out\""
  destination_arn = local.newrelic_log_ingestion_lambda
}

resource "aws_lambda_permission" "nr_lambda_permission_cognito_custom_msg" {
  statement_id  = "NRLambdaPermission_CognitoCustomMsg_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "arn:aws:logs:us-east-1:498823821309:log-group:/aws/lambda/${aws_lambda_function.cognito_custom_message.function_name}:*"
}
