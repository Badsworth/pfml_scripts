# Cross-account permissions for the FINEOS PFML AWS account to access data.
#
# See the following Confluence page for further discussion and details:
# https://lwd.atlassian.net/wiki/spaces/API/pages/454558837/Eligibility+feed+transfer+options
#
locals {
  fineos_account_id = "666444232783"
}

data "aws_iam_policy_document" "fineos_s3_access_policy" {
  for_each = toset(local.environments)

  statement {
    sid = "AllowS3ReadOnBucket"
    actions = [
      "s3:Get*",
      "s3:List*"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${each.key}-fineos-transfer",
      "arn:aws:s3:::massgov-pfml-${each.key}-fineos-transfer/*"
    ]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${local.fineos_account_id}:root"]
    }

    effect = "Allow"
  }
}
