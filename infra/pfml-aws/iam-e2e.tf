// This file creates a shared user for the E2E team to upload fake DOR data

locals {
  e2e_environments = ["test", "stage"]
}

// One user to access both the test and stage bucket
resource "aws_iam_user" "e2e_agency_transfer" {
  name = "pfml-end-to-end-agency-transfer"
}

data "aws_iam_policy_document" "e2e_dor_s3_access_policy" {
  for_each = toset(local.e2e_environments)

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

resource "aws_iam_policy" "e2e_dor_s3_access_policy" {
  for_each = toset(local.e2e_environments)
  name     = "e2e-dor-s3-access-policy-${each.key}"
  policy   = data.aws_iam_policy_document.e2e_dor_s3_access_policy[each.key].json
}

resource "aws_iam_user_policy_attachment" "e2e_dor_policy_attachment" {
  for_each   = toset(local.e2e_environments)
  user       = aws_iam_user.e2e_agency_transfer.name
  policy_arn = aws_iam_policy.e2e_dor_s3_access_policy[each.key].arn
}
