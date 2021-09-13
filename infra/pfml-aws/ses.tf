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
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-payments-fineos-process/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-payments-ctr-process/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-pub-payments-process-fineos/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-pub-payments-create-pub-files/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-pub-payments-process-pub-returns/*",
        "arn:aws:sts::${data.aws_caller_identity.current.account_id}:assumed-role/pfml-api-*-ecs-tasks-reductions-workflow/*",

        # Duplicate the roles above but in the normal IAM format.
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/mass-pfml-dua-email-automation-lambda-role",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-payments-fineos-process",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-payments-ctr-process",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-pub-payments-process-fineos",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-pub-payments-create-pub-files",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-pub-payments-process-pub-returns",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/pfml-api-*-ecs-tasks-reductions-workflow",

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
