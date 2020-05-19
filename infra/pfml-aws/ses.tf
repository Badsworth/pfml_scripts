# Setup SES to send emails

# 1. Add the email we want to send from
resource "aws_ses_email_identity" "noreply" {
  email = "noreplypfml@mass.gov"
}

# 2. Create policy that only allows Cognito to send emails from the email address
data "aws_iam_policy_document" "allow_cognito_ses_actions" {
  statement {
    effect    = "Deny"
    actions   = ["ses:*"]
    resources = [aws_ses_email_identity.noreply.arn]

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
  identity = aws_ses_email_identity.noreply.arn
  name     = "massgov-pfml-allow-cognito-send-email"
  policy   = data.aws_iam_policy_document.allow_cognito_ses_actions.json
}
