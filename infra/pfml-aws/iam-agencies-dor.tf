# The department of revenue (DOR) sends us data through an S3 bucket pushed from
# their MoveIT instance. This sets up their user.

#
# Create a user for DOR data.
#    After creating this user, generate an access key through the AWS console
#    and share it to a DOR representative over Interchange.
resource "aws_iam_user" "agency_department_of_revenue" {
  for_each = toset(local.vpcs)
  name     = "pfml-department-of-revenue-moveit-${each.key}"
}

// NOTE: If you change this policy, please also change the policy
// in iam-e2e.tf
data "aws_iam_policy_document" "dor_s3_access_policy" {
  for_each = toset(local.vpcs)

  statement {
    sid = "AllowDorListingOfBucket"
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
        "dor/",
        "dor/*"
      ]
    }

    effect = "Allow"
  }

  statement {
    sid = "AllowS3ReadOnBucket"
    actions = [
      "s3:Get*",
      "s3:List*"
    ]

    resources = [
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor/*",
    ]

    effect = "Allow"
  }

  statement {
    sid = "AllowS3WriteOnBucket"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor/*",
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
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor/*",
    ]

    effect = "Deny"
  }

  statement {
    sid = "ExplicitlyDenyAllForDOR"
    actions = [
      "*"
    ]

    not_resources = [
      aws_s3_bucket.agency_transfer[each.key].arn,
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor",
      "${aws_s3_bucket.agency_transfer[each.key].arn}/dor/*",
    ]

    effect = "Deny"
  }
}

resource "aws_iam_policy" "dor_s3_access_policy" {
  for_each = toset(local.vpcs)
  name     = "dor-s3-access-policy-${each.key}"
  policy   = data.aws_iam_policy_document.dor_s3_access_policy[each.key].json
}

resource "aws_iam_user_policy_attachment" "dor_policy_attachment" {
  for_each   = toset(local.vpcs)
  user       = aws_iam_user.agency_department_of_revenue[each.key].name
  policy_arn = aws_iam_policy.dor_s3_access_policy[each.key].arn
}
