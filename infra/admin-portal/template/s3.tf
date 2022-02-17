#
# S3 resources for hosting the Admin Portal website
#

resource "aws_s3_bucket" "admin_portal_web" {
  bucket = "massgov-${local.app_name}-${var.environment_name}-admin-portal-site-builds"

  # EOTSS AWS Tagging Standards
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-${local.app_name}-${var.environment_name}-admin-portal-site-builds"
    public      = "yes"
  })
}

# Block public access
resource "aws_s3_bucket_public_access_block" "admin_portal_web" {
  bucket = aws_s3_bucket.admin_portal_web.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "admin_portal_web" {
  statement {
    sid       = "PublicReadForGetBucketObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.admin_portal_web.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.admin_portal_web_origin_access_identity.iam_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "admin_portal_web_policy" {
  bucket = aws_s3_bucket.admin_portal_web.id
  policy = data.aws_iam_policy_document.admin_portal_web.json
}

# One bucket will be used to log all Admin Portal Cloudfront requests broken up by env prefixes
# Bucket is defined in infra/pfml-aws/s3.tf
data "aws_s3_bucket" "cloudfront_access_logging" {
  bucket = "massgov-pfml-admin-portal-cloudfront-logging"
}
