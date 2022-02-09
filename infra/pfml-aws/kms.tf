locals {
  envs = ["prod", "non-prod"]
}

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
      type        = "AWS"
      identifiers = module.constants.prod_admin_roles
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

data "aws_iam_policy_document" "allow_admin_groups_access_policy" {
  for_each = toset(local.envs)

  statement {
    sid = "AllowAllForAdmins"

    actions = [
      "kms:*",
    ]

    effect    = "Allow"
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = module.constants.prod_admin_roles
    }
  }
}

resource "aws_kms_key" "api_config_secrets" {
  for_each    = toset(local.envs)
  description = "Terraform generated KMS key for API config secrets in ${each.key}"
  policy      = data.aws_iam_policy_document.allow_admin_groups_access_policy[each.key].json
}

resource "aws_kms_alias" "api_config_secrets_aliases" {
  for_each      = toset(local.envs)
  name          = "alias/pfml-api-${each.key}-config-secrets"
  target_key_id = aws_kms_key.api_config_secrets[each.key].key_id
}

