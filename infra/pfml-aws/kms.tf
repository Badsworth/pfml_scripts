data "aws_iam_policy_document" "prod_tfstate_s3_kms_key" {
  # Allow read/write with KMS key

  statement {
    sid = "AllowAllForAdmins"

    actions = [
      "kms:*",
    ]

    effect    = "Allow"
    resources = ["*"]

    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
        "arn:aws:iam::498823821309:role/AWS-498823821309-Infrastructure-Admin",
        "arn:aws:iam::498823821309:role/ci-run-deploys",
        module.constants.infra_admin_sso_arn
      ]
    }
  }

}

resource "aws_kms_key" "s3_kms_key" {
  description = "Terraform generated KMS key for the massgov-pfml-prod-env-mgmt bucket"
  policy      = data.aws_iam_policy_document.prod_tfstate_s3_kms_key.json
}

resource "aws_kms_key" "ses_newrelic_dlq" {
  description = "Terraform generated KMS key for the massgov-pfml-ses-to-newrelic-dlq bucket"
}

resource "aws_kms_alias" "id_proofing_document_alias" {
  name          = "alias/prod_tfstate_s3_kms_key"
  target_key_id = aws_kms_key.s3_kms_key.key_id
}
