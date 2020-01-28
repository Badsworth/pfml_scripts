resource "aws_cognito_user_pool" "claimants_pool" {
  name                     = "massgov-pfml-${var.env_name}"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  sms_authentication_message = "Your authentication code is {####}. "

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  // TODO: Remove this hack once the bug fix is released.
  //       https://github.com/terraform-providers/terraform-provider-aws/issues/8827
  admin_create_user_config {
    unused_account_validity_days = 0
  }

  verification_message_template {
    default_email_option  = "CONFIRM_WITH_CODE"
    email_subject_by_link = "massgov-pfml-${var.env_name}: Your verification link"
    email_message_by_link = "Please click the link below to verify your email address. {##Verify Email##}"
    email_subject         = "massgov-pfml-${var.env_name}: Your verification code"
    email_message         = "Your verification code is {####}."
    sms_message           = "Your verification code is {####}."
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
  name         = "massgov-pfml-${var.env_name}"
  user_pool_id = aws_cognito_user_pool.claimants_pool.id

  callback_urls                = [var.cognito_redirect_url]
  default_redirect_uri         = var.cognito_redirect_url
  logout_urls                  = [var.cognito_logout_url]
  supported_identity_providers = ["COGNITO"]
  refresh_token_validity       = 30

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["phone", "email", "openid", "profile", "aws.cognito.signin.user.admin"]

  read_attributes  = ["email", "email_verified", "phone_number", "phone_number_verified", "updated_at"]
  write_attributes = ["email", "email_verified", "updated_at"]
}

resource "aws_cognito_user_pool_domain" "massgov_pfml_domain" {
  domain       = "massgov-pfml-${var.env_name}"
  user_pool_id = aws_cognito_user_pool.claimants_pool.id
}
