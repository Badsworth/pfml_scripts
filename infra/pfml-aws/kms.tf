
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
  # Below statement allows the prod_admin_roles (defined in constants/outputs.tf) full access to the KMS key
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
  # Below statement allows all roles in the respective environment full access to the KMS key
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
  # Below statement allows SNS topics to be encrypted at rest with their environment's respective KMS key
  statement {
    sid = "Allow_SNS_CW_EventBridge_Services"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*"
    ]
    effect    = "Allow"
    resources = ["*"]
    principals {
      type = "Service"
      identifiers = [
        "sns.amazonaws.com",
        "cloudwatch.amazonaws.com",
        "events.amazonaws.com"
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
  name          = "alias/massgov-pfml-${each.key}-kms-key"
  target_key_id = aws_kms_key.env_kms_key[each.key].key_id
}

# ----------------------------------------------------------------------------------------------------------------------------------------- #
# MassGov PFML Main KMS key for all resources to use that aren't environment restricted 
# If a resource (i.e. an S3 bucket) is created that won't belong to a specific environment and needs KMS permissions,
# the principle (Only Service principles since all AWS principals are explicitly allowed) will need to be added to the below KMS key policy. 
# All KMS permissions going forward will be handled through the KMS key policy instead of through the service's IAM role

resource "aws_kms_key" "main_kms_key" {
  description = "Terraform generated KMS key for resources that aren't environment restricted"
  policy      = data.aws_iam_policy_document.main_kms_key_policy.json
}

resource "aws_kms_alias" "main_kms_key_alias" {
  name          = "alias/massgov-pfml-main-kms-key"
  target_key_id = aws_kms_key.main_kms_key.key_id
}

data "aws_iam_policy_document" "main_kms_key_policy" {
  statement {
    sid = "AllowAllAWSPrincipals"

    actions = [
      "kms:*",
    ]

    effect    = "Allow"
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
  statement {
    sid = "AllowServicePrincipals"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*"
    ]
    effect    = "Allow"
    resources = ["*"]
    principals {
      type = "Service"
      identifiers = [
        "sns.amazonaws.com",
        "cloudwatch.amazonaws.com",
        "events.amazonaws.com"
      ]
    }
  }
  statement {
    sid = "AllowCloudtrailLogsToBeEncryptedAtRestUsingKMS"
    actions = [
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
      "kms:Decrypt",
      "kms:ReEncryptFrom"
    ]
    effect    = "Allow"
    resources = ["*"]
    principals {
      type = "Service"
      identifiers = [
        "s3.amazonaws.com",
        "cloudtrail.amazonaws.com"
      ]
    }
  }
}
# ----------------------------------------------------------------------------------------------------------------------------------------- #
