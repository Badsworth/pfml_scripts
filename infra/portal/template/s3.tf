#
# S3 resources for hosting the Portal website
#

resource "aws_s3_bucket" "portal_web" {
  bucket = "massgov-${local.app_name}-${var.environment_name}-portal-site-builds"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  # EOTSS AWS Tagging Standards
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-${local.app_name}-${var.environment_name}-portal-site-builds"
    public      = "yes"
  })
}

# Block public access
resource "aws_s3_bucket_public_access_block" "portal_web" {
  bucket = aws_s3_bucket.portal_web.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "portal_web" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.portal_web.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.portal_web_origin_access_identity.iam_arn]
    }
  }

  statement {
    sid     = "EnforceTls"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      "${aws_s3_bucket.portal_web.arn}/*",
      aws_s3_bucket.portal_web.arn
    ]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
    condition {
      test     = "NumericLessThan"
      variable = "s3:TlsVersion"
      values   = ["1.2"]
    }
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "portal_web_policy" {
  bucket = aws_s3_bucket.portal_web.id
  policy = data.aws_iam_policy_document.portal_web.json
}

# One bucket will be used to log all Portal Cloudfront requests broken up by env prefixes
# Bucket is defined in infra/pfml-aws/s3.tf
data "aws_s3_bucket" "cloudfront_access_logging" {
  bucket = "massgov-pfml-portal-cloudfront-logging"
}
