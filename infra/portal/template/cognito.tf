resource "aws_cognito_user_pool" "claimants_pool" {
  name                     = "massgov-${local.app_name}-${var.environment_name}"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  email_configuration {
    # Use this SES email to send cognito emails. If we're not using SES for emails then use null
    source_arn            = var.ses_email_address == "" ? null : "arn:aws:ses:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:identity/${var.ses_email_address}"
    email_sending_account = var.ses_email_address == "" ? "COGNITO_DEFAULT" : "DEVELOPER"
    # Customize the name that users see in the "From" section of their inbox, so that it's clearer who the email is from
    from_email_address = var.ses_email_address == "" ? null : "Mass.gov <${var.ses_email_address}>"
  }

  sms_authentication_message = "Your authentication code is {####}. "

  lambda_config {
    custom_message = aws_lambda_function.cognito_custom_message.arn
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
  refresh_token_validity       = 30

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
  handler          = "lambda.handler"
  role             = aws_iam_role.lambda_basic_executor.arn
  runtime          = "nodejs12.x"
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
