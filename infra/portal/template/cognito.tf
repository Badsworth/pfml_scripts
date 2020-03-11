locals {
  // Domain set up through Cloudfront and Route53.
  // This will be used as Cognito's signin and logout redirect URLs.
  hosted_domain = "https://${aws_route53_record.root_v6.fqdn}"
}

resource "aws_cognito_user_pool" "claimants_pool" {
  name                     = "massgov-pfml-${var.env_name}"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  sms_authentication_message = "Your authentication code is {####}. "

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  verification_message_template {
    default_email_option  = "CONFIRM_WITH_CODE"
    email_subject_by_link = "Activate your Paid Family and Medical Leave account"
    email_message_by_link = <<-EOT
      To verify your email address and activate your Paid Family and Medical Leave account, please click the following link: {##Verify Email##}

      This link is only valid for 24 hours.

      This is an automatically generated message from the Commonwealth of Massachussets. Replies are not monitored or answered.
      EOT
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

  callback_urls                = concat(var.cognito_extra_redirect_urls, [local.hosted_domain])
  logout_urls                  = concat(var.cognito_extra_logout_urls, [local.hosted_domain])
  supported_identity_providers = ["COGNITO"]
  refresh_token_validity       = 30

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["phone", "email", "openid", "profile", "aws.cognito.signin.user.admin"]

  read_attributes  = ["email", "email_verified", "phone_number", "phone_number_verified", "updated_at"]
  write_attributes = ["email", "updated_at"]
}

resource "aws_cognito_user_pool_domain" "massgov_pfml_domain" {
  domain       = "massgov-pfml-${var.env_name}"
  user_pool_id = aws_cognito_user_pool.claimants_pool.id
}
