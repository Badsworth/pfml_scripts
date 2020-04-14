# Setup SES to send authentication emails from Cognito

# 1. Add the email we want to send from
resource "aws_ses_email_identity" "cognito_sender_email" {
  # Only create this resource if we're using SES for sending emails
  count = var.cognito_use_ses_email ? 1 : 0
  email = var.cognito_sender_email
}

# 2. Create policy that only allows Cognito to send emails from the email address
data "aws_iam_policy_document" "allow_cognito_ses_actions" {
  count = var.cognito_use_ses_email ? 1 : 0

  statement {
    effect    = "Deny"
    actions   = ["ses:*"]
    resources = [aws_ses_email_identity.cognito_sender_email[0].arn]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "ArnNotEquals"
      variable = "aws:PrincipalArn"
      # Service-linked role used by Cognito to send emails
      # https://docs.aws.amazon.com/cognito/latest/developerguide/using-service-linked-roles.html#slr-permissions
      values = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/email.cognito-idp.amazonaws.com/AWSServiceRoleForAmazonCognitoIdpEmailService"]
    }
  }
}

# 3. Set the SES Sending Authorization policy
# See: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-authorization-policies.html
resource "aws_ses_identity_policy" "allow_cognito_ses_actions" {
  count    = var.cognito_use_ses_email ? 1 : 0
  identity = aws_ses_email_identity.cognito_sender_email[0].arn
  name     = "${local.app_name}-${var.environment_name}-allow-cognito-send-email"
  policy   = data.aws_iam_policy_document.allow_cognito_ses_actions[0].json
}
