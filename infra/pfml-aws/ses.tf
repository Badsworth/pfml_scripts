# See /docs/api/ses.tf for full details on configuring SES permissions for applications.
#
locals {
  email_identities = {
    "noreplypfml"            = aws_ses_email_identity.noreply.arn,
    "pfmldonotreply-massgov" = aws_ses_email_identity.pfml_donotreply.arn,
    "pfmldonotreply-statema" = aws_ses_email_identity.pfml_donotreply_state.arn,
  }
}

# Deprecated email identity
resource "aws_ses_email_identity" "noreply" {
  email = "noreplypfml@mass.gov"
}

# New email domain and identity -- see https://lwd.atlassian.net/browse/PFMLPB-640.
#
resource "aws_ses_domain_identity" "eol" {
  domain = "eol.mass.gov"
}

resource "aws_ses_domain_dkim" "eol" {
  domain = aws_ses_domain_identity.eol.domain
}

resource "aws_ses_email_identity" "pfml_donotreply" {
  email = "PFML_DoNotReply@eol.mass.gov"
}

# Deprecated email alias
resource "aws_ses_domain_identity" "eol_state" {
  domain = "eol.state.ma.us"
}

resource "aws_ses_domain_dkim" "eol_state" {
  domain = aws_ses_domain_identity.eol_state.domain
}

resource "aws_ses_email_identity" "pfml_donotreply_state" {
  email = "PFML_DoNotReply@eol.state.ma.us"
}

# For readability, this HTML template is managed at portal/template/emails
# To get it in a format usable in Terraform, first edit there and then run 
# tr -ds '\n' '[:space:]' < ../portal/template/emails/mfa-disabled.html | sed "s/\"/'/g" 
# this command will put it in a single string format for this part of the code
resource "aws_ses_template" "disabled_mfa_template" {
  name    = "MfaHasBeenDisabled"
  subject = "SMS verification codes have been disabled for your account"
  html    = "<table width='100%' style='font-family: Open Sans,HelveticaNeue,Helvetica,Arial,sans-serif;font-size: 16px;text-align: left;'cellpadding='0'cellspacing='0'><tbody> <tr> <td style='background: #14558f; height: 24px'></td> </tr> <tr> <td style='background: #be5817; padding: 16px 32px;'> <table align='center' cellspacing='0' style='max-width: 600px;' width='100%'> <tbody> <tr> <td> <img alt='Massachusetts Paid Family and Medical Leave' src='https://mcusercontent.com/0757f7959581770082e8f2fd9/images/4665cf36-af48-4bce-9032-33a7786052de.png' width='264' style='padding-bottom: 0;' class='mcnImage' /> </td> </tr> </tbody> </table> </td> </tr> <tr> <td> <table align='center' style='line-height: 150%; text-align: left; max-width: 600px; color:#535353;padding-bottom: 32px;' width='100%'> <tbody> <tr> <td style='padding: 32px;'> <p style=''> A verification code will no longer be sent by text message to the phone number ending in {{phone_number_last_four}} when you log into your account at paidleave.mass.gov. <br/> <br/> If you requested this, no action is required. </br/> </br/> If you did not request this, go to paidleave.mass.gov and follow the Forgot your password? steps to change your password and protect your account. </br/> </br/> To re-enable verification codes, log into your account and go to your Settings page. In the future, you will need this feature to access certain information like tax documents. </p> </td> </tr> </tbody> </table> </td> </tr> <tr> <td style='background: #FAFAFA; border-top: 3px solid #EAEAEA;'> <table align='center' style='max-width: 600px;' width='100%'> <tbody> <tr> <td> <img align='center' alt='' src='https://mcusercontent.com/0757f7959581770082e8f2fd9/images/a163a15d-9150-4959-9b02-998caa00bca4.png' width='564' style='max-width: 903px; padding: 0 18px; display: inline; vertical-align: bottom;' /> </td> </tr> <tr> <td style='padding:0px 18px 9px; text-align: left; color: #656565; font-size: 12px;'> <div> <a href='https://www.mass.gov/orgs/department-of-family-and-medical-leave' rel='noopener' target='_blank' data-saferedirecturl='https://www.google.com/url?hl=en&amp;q=https://www.mass.gov/orgs/department-of-family-and-medical-leave&amp;source=gmail&amp;ust=1607720450081000&amp;usg=AFQjCNF21ULm-5y7N8G5cZXEVu-uHldNPg'> Department of Family & Medical Leave </a> </div> <div>P.O. Box 838, Lawrence, MA 01842</div> <div>(833) 344-7365 from 8am–5pm ET</div> </td> </tr> <tr> <td style='font-size: 12px; font-style: italic; padding: 18px;'> This e-mail message is for the sole use of the intended recipient and may contain confidential and privileged information. Any unauthorized review, use, disclosure, or distribution is strictly prohibited. If you are not the intended recipient, please contact us at (833) 344-7365 from 8am–5pm ET and then destroy all copies of the original message. </td> </tr> </tbody> </table> </td> </tr></tbody></table>"
  text    = "A verification code will no longer be sent by text message to the phone number ending in {{phone_number_last_four}} when you log into your account at paidleave.mass.gov. If you requested this, no action is required. If you did not request this, go to paidleave.mass.gov and follow the Forgot your password? steps to change your password and protect your account. To re-enable verification codes, log into your account and go to your Settings page. In the future, you will need this feature to access certain information like tax documents."
}

# Create an IAM policy that only allows Cognito and payments tasks to send emails from the email address
data "aws_iam_policy_document" "restrict_ses_senders" {
  for_each = local.email_identities

  statement {
    effect = "Deny"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    resources = [each.value]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "ArnNotLike"
      variable = "aws:PrincipalArn"
      values = [
        # Service-linked role used by Cognito to send emails
        # https://docs.aws.amazon.com/cognito/latest/developerguide/using-service-linked-roles.html#slr-permissions
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/email.cognito-idp.amazonaws.com/AWSServiceRoleForAmazonCognitoIdpEmailService",
        # Payments and Reductions ECS tasks created in infra/ecs-tasks.
        # Since ecs tasks are created after the fact, we hardcode their ARNs here.
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/mass-pfml-dua-email-automation-lambda-role/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-pub-payments-process-fineos/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-pub-payments-create-pub-files/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-pub-payments-process-pub-returns/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-reductions-workflow/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-mfa-lockout-resolution/*",

        # Duplicate the roles above but in the normal IAM format.
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/mass-pfml-dua-email-automation-lambda-role",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-pub-payments-process-fineos",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-pub-payments-create-pub-files",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-pub-payments-process-pub-returns",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-reductions-workflow",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-mfa-lockout-resolution",

        # Add in existing AWS users with SES in their name, as of April 8, 2021.
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/pfml-ses-savilinx-sn-prod-user",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/pfml-ses-third-party-smtp-user",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/pfml-ses-savilinx-sn-test-user",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/pfml-ses-mailchimp-test-user"
      ]
    }
  }
}

# Set the SES Sending Authorization policy
# See: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-authorization-policies.html
resource "aws_ses_identity_policy" "restrict_ses_senders" {
  for_each = local.email_identities

  identity = each.value
  name     = "massgov-pfml-restrict-ses-send-email-${each.key}"
  policy   = data.aws_iam_policy_document.restrict_ses_senders[each.key].json
}
