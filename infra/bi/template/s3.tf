# LWD Roles that need to access the S3 bucket staged for redshift
locals {
  nonprod_roles = [
    "arn:aws:iam::018311717589:role/aws-service-role/redshift.amazonaws.com/AWSServiceRoleForRedshift",
    "arn:aws:iam::018311717589:role/pfml-all-redshift-s3-daily-import-role",
    "arn:aws:iam::018311717589:role/redshiftSpectrumRole"
  ]
  prod_roles = [
    "arn:aws:iam::018311717589:role/redshift-lwd-prod-cluster-edw-role",
    "arn:aws:iam::018311717589:role/pfml-all-redshift-s3-daily-import-role"
  ]
}
data "aws_iam_policy_document" "bi_imports_bucket_policy_document" {
  statement {
    sid = "LWD RedShift Access to Bucket"

    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.bi_reporting_lambda_role.arn]
    }

    principals {
      type        = "AWS"
      identifiers = var.environment_name == "prod" ? local.prod_roles : local.nonprod_roles
    }

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:GetObject"
    ]

    resources = [
      aws_s3_bucket.bi_imports.arn,
      "${aws_s3_bucket.bi_imports.arn}/*"
    ]
  }
}

# KMS key policy for:
# - allowing the LWD account roles to decrypt files in the S3 bucket
# - allowing the lambda to encrypt files when uploading to the S3 bucket
data "aws_iam_policy_document" "bi_imports_s3_kms_key_policy" {
  statement {
    sid    = "LWD account KMS Key decrypt"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = var.environment_name == "prod" ? local.prod_roles : local.nonprod_roles
    }
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::498823821309:root",
        aws_iam_role.bi_reporting_lambda_role.arn
      ]
    }
    actions = [
      "kms:*",
      "s3:List*",
      "s3:Get*"
    ]
    resources = [
      "arn:aws:kms:us-east-1:498823821309:key/*"
    ]
  }
}

resource "aws_s3_bucket" "bi_imports" {
  bucket = "massgov-pfml-${var.environment_name}-redshift-daily-import"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.s3_kms_key.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }

  versioning {
    enabled = "false"
  }


  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
    Name        = "massgov-pfml-${var.environment_name}-redshift-daily-import"
  })
}



resource "aws_s3_bucket_policy" "bi_imports_bucket_policy" {
  bucket = aws_s3_bucket.bi_imports.id
  policy = data.aws_iam_policy_document.bi_imports_bucket_policy_document.json
}

resource "aws_kms_key" "s3_kms_key" {
  description = "KMS key for Redshift S3 buckets"
  policy      = data.aws_iam_policy_document.bi_imports_s3_kms_key_policy.json
}

resource "aws_kms_alias" "s3_kms_key_alias" {
  name          = "alias/mass-pfml-${var.environment_name}-redshift-daily-import-s3-key"
  target_key_id = aws_kms_key.s3_kms_key.arn
}

resource "aws_s3_bucket_public_access_block" "bi_imports_block_public_access" {
  bucket = aws_s3_bucket.bi_imports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}