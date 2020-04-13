# Sets up access policies for developers on the team.
#
# We manage this through terraform to:
# 1) allow developers to request access changes themselves.
# 2) document why they needed the additional access.
#
# For developers:
#   If you need additional access, please create a PR
#   with your reasoning and use cases.
#
# For full-access AWS admins:
#   Once the changes are merged, you must run the changes
#   manually with your elevated role.
#
data "aws_iam_role" "developers" {
  name = "AWS-498823821309-Infrastructure-Admin"
}

data "aws_iam_policy_document" "developers_access_policy" {
  statement {
    actions = [
      # Allow access the terraform_locks table in DynamoDB.
      "dynamodb:GetItem",
      "dynamodb:PutItem",

      # Allow domain certificate lookups.
      "acm:Describe*",
      "acm:Get*",
      "acm:List*",

      # Allow teams to configure logging and monitoring.
      "cloudtrail:*",
      "cloudwatch:*",
      "logs:*",

      # Allow teams to manage secrets in SSM Parameter Store.
      "ssm:*",

      # Allow teams to look at IAM users and roles; additional (restricted)
      # write access is provided in a separate statement/policy.
      "iam:Get*",

      # Allow teams to use KMS encryption keys.
      "kms:*",

      # Allow teams to read and store data in S3. Also allows the Portal
      # team to deploy the application to S3-hosted buckets.
      "s3:*",

      # Allow the Portal team to set up the Portal application, including:
      # - Cloudfront distributions of the statically-built files.
      # - Cognito user authentication.
      # - Simple Email Service for sending information to folks using the Portal.
      "cloudfront:*",
      "cognito-idp:*",
      "ses:*",

      # Allow API team to set up the API, including:
      # - API Gateway and load balancing
      # - Docker container management on ECR + ECS
      # - RDS data storage
      # - Lambdas for data pipelining.
      "apigateway:*",
      "ecr:*",
      "ecs:*",
      "elasticloadbalancing:*",
      "rds:*",
      "lambda:*"
    ]

    resources = [
      "*"
    ]
  }

  # Allow individuals to request direct support from AWS, e.g.
  # for requesting new limits on services that our applications use.
  statement {
    actions = [
      "support:*"
    ]

    resources = [
      "*"
    ]
  }
}

data "aws_iam_policy_document" "developers_and_ci_iam_policy" {
  # Allow access to create, update, and delete any IAM roles that weren't created by EOTSS.
  #
  # This also includes the iam:CreateServiceLinkedRole permission, which is needed
  # to create Cognito user pools.
  statement {
    sid     = "NewIamRolesAccess"
    actions = ["iam:*"]
    not_resources = [
      "arn:aws:iam::498823821309:role/ADFS-*",
      "arn:aws:iam::498823821309:role/AWS-498823821309-*",
      "arn:aws:iam::498823821309:role/EOTSS-*",
      "arn:aws:iam::498823821309:role/eotss_*",
      "arn:aws:iam::498823821309:role/EOLWD-PFML-VPC-FlowLogs",
      "arn:aws:iam::498823821309:role/VPCFlowLogStack-*",
      "arn:aws:iam::498823821309:role/workspaces_DefaultRole",
      "arn:aws:iam::498823821309:role/us-east-1-config-role",
      "arn:aws:iam::498823821309:role/tss-soe-softwarecompliance",
      "arn:aws:iam::498823821309:role/EOL-SOE-*",
      "arn:aws:iam::498823821309:role/SOE-*",
      "arn:aws:iam::498823821309:role/soe-*",
      "arn:aws:iam::498823821309:role/smx-*",
      "arn:aws:iam::498823821309:role/AWSCloudFormationStackSetExecutionRole",
      "arn:aws:iam::498823821309:role/lambda_s3_access",
      "arn:aws:iam::498823821309:role/idaptive-Admin",
      "arn:aws:iam::498823821309:role/AWS_Events_Invoke_Event_Bus_*"
    ]
  }
}

resource "aws_iam_policy" "developers_access_policy" {
  name        = "infrastructure-admin-access-policy"
  description = "Write-centric access policies for infrastructure admins"
  policy      = data.aws_iam_policy_document.developers_access_policy.json
}

resource "aws_iam_policy" "developers_and_ci_iam_policy" {
  name        = "infrastructure-admin-and-github-actions-iam-policy"
  description = "Write-centric access policies for infrastructure admins and Github Actions"
  policy      = data.aws_iam_policy_document.developers_and_ci_iam_policy.json
}

resource "aws_iam_policy_attachment" "developers_access_policy_attachment" {
  name       = "infrastructure-admin-access-policy-attachment"
  roles      = [data.aws_iam_role.developers.id]
  policy_arn = aws_iam_policy.developers_access_policy.arn
}

resource "aws_iam_policy_attachment" "developers_and_ci_iam_policy_attachment" {
  name       = "infrastructure-admin-and-github-actions-iam-policy-attachment"
  roles      = [data.aws_iam_role.developers.id]
  policy_arn = aws_iam_policy.developers_and_ci_iam_policy.arn
}
