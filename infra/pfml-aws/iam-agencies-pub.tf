# The People's United Bank (PUB) system is our payments system.
# This sets up the user that is needed for retrieving and returning files to our system.
#
# pfml-pub-moveit-nonprod: Access to all lower environment agency-transfer/pub/* folders.
# pfml-pub-moveit-prod: Access to the prod agency-transfer/pub/* folders.
#

# Create a user for PUB data.
#    After creating this user, generate an access key through the AWS console
#    and share it to a representative over Interchange.
resource "aws_iam_user" "agency_pub" {
  for_each = toset(local.vpcs)
  name     = "pfml-pub-moveit-${each.key}"
}

# Create an access policy for each environment.
# All of the lower environments will be attached to the nonprod user.
locals {
  # Define the list of S3 buckets accessible by the pub user for nonprod and prod
  nonprod_envs        = setsubtract(toset(local.environments), ["prod", "infra-test"])
  nonprod_bucket_arns = [for env in local.nonprod_envs : aws_s3_bucket.agency_transfer[env].arn]
  prod_bucket_arns    = [aws_s3_bucket.agency_transfer["prod"].arn]

  bucket_arns = {
    "nonprod" = local.nonprod_bucket_arns,
    "prod"    = local.prod_bucket_arns
  }
}

data "aws_iam_policy_document" "pub_s3_access_policy" {
  for_each = toset(local.vpcs)

  statement {
    sid = "AllowPubListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = local.bucket_arns[each.key]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "pub/",
        "pub/*"
      ]
    }

    effect = "Allow"
  }

  statement {
    sid = "AllowS3ReadDeleteOnBucket"
    actions = [
      "s3:Get*",
      "s3:List*",
      "s3:DeleteObject"
    ]

    resources = flatten([for bucket_arn in local.bucket_arns[each.key] : [
      "${bucket_arn}/pub/outbound",
      "${bucket_arn}/pub/outbound/*",
    ]])

    effect = "Allow"
  }

  statement {
    sid = "AllowS3WriteOnBucket"
    actions = [
      "s3:List*",
      "s3:PutObject",
      "s3:AbortMultipartUpload"
    ]

    resources = flatten([for bucket_arn in local.bucket_arns[each.key] : [
      "${bucket_arn}/pub/inbound",
      "${bucket_arn}/pub/inbound/*",
    ]])

    effect = "Allow"
  }

  statement {
    sid = "ExplicitlyDenyOtherOpsOnBucket"
    not_actions = [
      "s3:*"
    ]

    resources = flatten([for bucket_arn in local.bucket_arns[each.key] : [
      bucket_arn,
      "${bucket_arn}/pub",
      "${bucket_arn}/pub/*",
    ]])

    effect = "Deny"
  }
}

# Create a policy for nonprod
resource "aws_iam_policy" "pub_s3_access_policy_nonprod" {
  name   = "pub-s3-access-policy-nonprod"
  policy = data.aws_iam_policy_document.pub_s3_access_policy["nonprod"].json
}

# Attach the nonprod policy to the nonprod user.
resource "aws_iam_user_policy_attachment" "pub_policy_attachment_nonprod" {
  user       = aws_iam_user.agency_pub["nonprod"].name
  policy_arn = aws_iam_policy.pub_s3_access_policy_nonprod.arn
}

# Create a prod policy
resource "aws_iam_policy" "pub_s3_access_policy_prod" {
  name   = "pub-s3-access-policy-prod"
  policy = data.aws_iam_policy_document.pub_s3_access_policy["prod"].json
}

# Attach the prod policy to the prod user.
resource "aws_iam_user_policy_attachment" "pub_policy_attachment_prod" {
  user       = aws_iam_user.agency_pub["prod"].name
  policy_arn = aws_iam_policy.pub_s3_access_policy_prod.arn
}
