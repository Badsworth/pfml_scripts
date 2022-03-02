
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

data "aws_iam_policy_document" "env_kms_key_policy" {
  for_each = toset(local.environments)
  statement {
    sid = "AllowAllForAdmins"

    actions = [
      "kms:*",
    ]

    effect    = "Allow"
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = each.key == "prod" ? module.constants.prod_admin_roles : module.constants.nonprod_admin_roles
    }
  }
  statement {
    sid = "AllowAllFor${each.key}Env"

    actions = [
      "kms:*",
    ]

    effect    = "Allow"
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:PrincipalArn"
      values = [
        "arn:aws:iam::498823821309:role/pfml-api-${each.key}-*",
        "arn:aws:iam::498823821309:role/pfml-${each.key}-*",
        "arn:aws:iam::498823821309:role/massgov-pfml-${each.key}-*"
      ]
    }
  }
}

resource "aws_kms_key" "env_kms_key" {
  for_each    = toset(local.environments)
  description = "Terraform generated KMS key for ${each.key}"
  policy      = data.aws_iam_policy_document.env_kms_key_policy[each.key].json
}

resource "aws_kms_alias" "env_kms_key_alias" {
  for_each      = toset(local.environments)
  name          = "alias/pfml-${each.key}-kms-key"
  target_key_id = aws_kms_key.env_kms_key[each.key].key_id
}

