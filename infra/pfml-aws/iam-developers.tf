# Sets up extra admin-y access policies for developers on the team,
# like full write access to SSM.
#
# TODO (INFRA-561) Remove this entire file; these SSO permissions are obsolete after July 1st, 2021
data "aws_iam_role" "developers" {
  name = "AWS-498823821309-Infrastructure-Admin"
}

data "aws_iam_policy_document" "developers_access_policy" {
  statement {
    actions = [
      # Allow individuals to view AWS health statuses affecting our resources.
      "health:*",

      # Allow individuals to manage secrets in SSM Parameter Store.
      "ssm:*",

      # Allow individuals to request direct support from AWS, e.g.
      # for requesting new limits on services that our applications use.
      "support:*",

      # Allow access to performance insights
      "pi:*"
    ]

    resources = [
      "*"
    ]
  }

  statement {
    sid = "FINEOSAssumeRoleAccess"
    actions = [
      # Allow individuals to assume the FINEOS cross-account role in test/stage.
      "sts:AssumeRole",
      "sts:TagSession"
    ]

    resources = [
      "arn:aws:iam::666444232783:role/somdev-IAMRoles-CustomerAccountAccessRole-BF05IBJSG74B",
      "arn:aws:iam::016390658835:role/sompre-IAMRoles-CustomerAccountAccessRole-S0EP9ABIA02Z"
    ]
  }

  statement {
    sid = "CiIamRoleAccess"
    actions = [
      "iam:*",
    ]

    resources = [
      "${aws_iam_role.ci_run_deploys.arn}"
    ]
  }
}

resource "aws_iam_policy" "developers_access_policy" {
  name        = "infrastructure-admin-access-policy"
  description = "Write-centric access policies for infrastructure admins"
  policy      = data.aws_iam_policy_document.developers_access_policy.json
}

resource "aws_iam_role_policy_attachment" "developers_access_policy_attachment" {
  role       = data.aws_iam_role.developers.id
  policy_arn = aws_iam_policy.developers_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "developers_deploy_access_policy_attachment" {
  role       = data.aws_iam_role.developers.id
  policy_arn = aws_iam_policy.developers_and_ci_deploy_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "developers_iam_policy_attachment" {
  role       = data.aws_iam_role.developers.id
  policy_arn = aws_iam_policy.developers_and_ci_iam_policy.arn
}
