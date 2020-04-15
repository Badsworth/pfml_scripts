# Sets up extra admin-y access policies for developers on the team,
# like full write access to SSM.
#
data "aws_iam_role" "developers" {
  name = "AWS-498823821309-Infrastructure-Admin"
}

data "aws_iam_policy_document" "developers_access_policy" {
  statement {
    actions = [
      # Allow individuals to manage secrets in SSM Parameter Store.
      "ssm:*",

      # Allow individuals to request direct support from AWS, e.g.
      # for requesting new limits on services that our applications use.
      "support:*"
    ]

    resources = [
      "*"
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
