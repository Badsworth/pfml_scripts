# Sets up a user and access policy role for CI/CD.
#
# The "pfml-github-actions" user itself has no permissions, but can assume the ci-run-deploys role along
# with PFML admins and developers. This allows us to easily test whether CI has all the read and write
# permissions it needs without having the long-term pfml-github-actions user credentials on our machines.
#
# This is particularly important because developers receive full read-only access by default, and
# pfml-github-actions does not.
#
# For PFML admins and developers that want to assume the role (i.e. pretend to be github actions),
# see the infra/README.md for details.
#
# Access for the role covers the following:
# - full access to services used by our applications.
# - full access to IAM, except for roles and users that were given to us by EOTSS.
#
# Most of this access comes from iam-shared.tf.
#
resource "aws_iam_user" "github_actions" {
  name = "pfml-github-actions"

  tags = {
    repo = "EOLWD/pfml"
  }
}

# 1. Generate a user access key that is exposed in the terraform state and should be set in Github Actions.
#
resource "aws_iam_access_key" "github_actions" {
  user = aws_iam_user.github_actions.name
}

# 2. Create a role that can be assumed by PFML developers, admins, and the pfml-github-actions user.
#
resource "aws_iam_role" "ci_run_deploys" {
  name               = "ci-run-deploys"
  assume_role_policy = data.aws_iam_policy_document.trust_assume_role_policy.json
}

data "aws_iam_policy_document" "trust_assume_role_policy" {
  statement {
    sid     = "PFMLDeveloperAssumeRole"
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
        "arn:aws:iam::498823821309:role/AWS-498823821309-Infrastructure-Admin",
        aws_iam_user.github_actions.arn,
      ]
    }
  }
}

# 3. Setup deploy permissions that are shared between developers and CI.
#
resource "aws_iam_role_policy_attachment" "ci_deploy_access_policy_attachment" {
  role       = aws_iam_role.ci_run_deploys.id
  policy_arn = aws_iam_policy.developers_and_ci_deploy_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "ci_iam_policy_attachment" {
  role       = aws_iam_role.ci_run_deploys.id
  policy_arn = aws_iam_policy.developers_and_ci_iam_policy.arn
}

# 4. Setup additional permissions for CI to run deploys with some restrictions.
#
data "aws_iam_policy_document" "ci_run_deploys_policy" {
  statement {
    sid = "PfmlAppsAccess"
    actions = [
      # Allow CI to read VPCs and subnets.
      "ec2:DescribeSubnets",
      "ec2:DescribeVpc*",

      # Allow CI to configure VPC endpoints.
      "ec2:CreateVpcEndpointServiceConfiguration",
      "ec2:DeleteVpcEndpointServiceConfigurations",
      "ec2:DescribeVpcEndpointServiceConfigurations",
      "ec2:ModifyVpcEndpointServicePermissions",

      # SSM is required to pull down database passwords, which are used
      # when generating the database itself or when updating the password
      # through a rotation.
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]

    resources = [
      "*"
    ]
  }
}

resource "aws_iam_policy" "ci_run_deploys_policy" {
  name        = "ci-run-deploys-policy"
  description = "For use by CI/CD to manage services that are in use within PFML applications."
  policy      = data.aws_iam_policy_document.ci_run_deploys_policy.json
}

resource "aws_iam_role_policy_attachment" "ci_run_deploys_policy_attachment" {
  role       = aws_iam_role.ci_run_deploys.id
  policy_arn = aws_iam_policy.ci_run_deploys_policy.arn
}
