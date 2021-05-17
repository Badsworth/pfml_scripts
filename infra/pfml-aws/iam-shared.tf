# Set up policies for deployments that are shared between developers and CI.
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
data "aws_iam_policy_document" "developers_and_ci_deploy_access_policy" {
  # TODO: This is probably more wide-ranging than it needs to be,
  #       and can be more granular in scope for certain services.
  statement {
    actions = [
      # Allow access the terraform_locks table in DynamoDB.
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",

      # Allow domain certificate lookups.
      "acm:Describe*",
      "acm:Get*",
      "acm:List*",
      "acm:AddTagsToCertificate",

      # Allow teams to configure logging and monitoring.
      "cloudtrail:*",
      "cloudwatch:*",
      "logs:*",

      # Allow teams to read and set Cloudwatch event rules.
      "events:*",

      # Allow teams to look at IAM users and roles; additional (restricted)
      # write access is provided in a separate statement/policy.
      "iam:Get*",

      # Allow teams to use KMS encryption keys.
      "kms:*",

      # Allow teams to read and store data in S3. Also allows the Portal
      # team to deploy the application to S3-hosted buckets.
      "s3:*",

      # Allow teams to manage SNS topics and subscriptions.
      "sns:*",

      # Allow teams to manage security groups.
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:CreateSecurityGroup",
      "ec2:DeleteSecurityGroup",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",

      # Allow teams to configure VPC endpoints for network privacy.
      "ec2:CreateVpcEndpoint",
      "ec2:DeleteVpcEndpoints",
      "ec2:DescribeVpcEndpoints",
      "ec2:DescribeVpcEndpointServices",
      "ec2:ModifyVpcEndpoint",
      "ec2:DescribePrefixLists",

      # Allow teams to configure Lambda ENIs.
      "ec2:CreateNetworkInterface",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DetachNetworkInterface",

      # Allow teams to configure VPC Links for network privacy.
      "ec2:CreateVpcEndpointServiceConfiguration",
      "ec2:DeleteVpcEndpointServiceConfigurations",
      "ec2:DescribeVpcEndpointServiceConfigurations",
      "ec2:ModifyVpcEndpointServicePermissions",

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
      # - Web Application Firewall (WAF)
      # - Firehose (for WAF logs)
      "apigateway:*",
      "ecr:*",
      "ecs:*",
      "elasticloadbalancing:*",
      "rds:*",
      "lambda:*",
      "application-autoscaling:*",
      "wafv2:*",
      "waf-regional:*",
      "firehose:*",
      "kinesis:*",

      # Allow Infra Admins to view resources associated with WAF ACL
      "appsync:ListGraphqlApis",

      # Allow API team to deploy Step Functions, such as the DOR Import.
      "states:*",

      # Allow teams to deploy CloudFormation stacks to manage resources
      # Terraform can not
      "cloudformation:*",

      # Allow listing of IAM role policies
      "iam:ListRolePolicies"
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
      "arn:aws:iam::498823821309:role/AWS_Events_Invoke_Event_Bus_*",
      "${aws_iam_role.ci_run_deploys.arn}"
    ]
  }
}

resource "aws_iam_policy" "developers_and_ci_deploy_access_policy" {
  name        = "infrastructure-admin-and-ci-deploy-access-policy"
  description = "Access policies for deploying PFML applications"
  policy      = data.aws_iam_policy_document.developers_and_ci_deploy_access_policy.json
}

resource "aws_iam_policy" "developers_and_ci_iam_policy" {
  name        = "infrastructure-admin-and-ci-iam-policy"
  description = "IAM access policies for infrastructure admins and Github Actions"
  policy      = data.aws_iam_policy_document.developers_and_ci_iam_policy.json
}
