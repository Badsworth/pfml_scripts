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
data "aws_iam_policy_document" "pub_s3_access_policy" {
  for_each = toset(local.environments)

  statement {
    sid = "AllowPubListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.agency_transfer[each.key].arn
    ]

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

    resources = [
      "${aws_s3_bucket.agency_transfer[each.key].arn}/pub/outbound",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/pub/outbound/*",
    ]

    effect = "Allow"
  }

  statement {
    sid = "AllowS3WriteOnBucket"
    actions = [
      "s3:List*",
      "s3:PutObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${aws_s3_bucket.agency_transfer[each.key].arn}/pub/inbound",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/pub/inbound/*",
    ]

    effect = "Allow"
  }

  statement {
    sid = "ExplicitlyDenyOtherOpsOnBucket"
    not_actions = [
      "s3:*"
    ]

    resources = [
      aws_s3_bucket.agency_transfer[each.key].arn,
      "${aws_s3_bucket.agency_transfer[each.key].arn}/pub",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/pub/*",
    ]

    effect = "Deny"
  }
}

# Create a policy for each lower environment
resource "aws_iam_policy" "pub_s3_access_policy_nonprod" {
  for_each = setsubtract(toset(local.environments), ["prod"])
  name     = "pub-s3-access-policy-${each.key}"
  policy   = data.aws_iam_policy_document.pub_s3_access_policy[each.key].json
}

# Attach all the lower environment policies to the nonprod user.
resource "aws_iam_user_policy_attachment" "pub_policy_attachment_nonprod" {
  for_each   = setsubtract(toset(local.environments), ["prod", "infra-test"])
  user       = aws_iam_user.agency_pub["nonprod"].name
  policy_arn = aws_iam_policy.pub_s3_access_policy_nonprod[each.key].arn
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
