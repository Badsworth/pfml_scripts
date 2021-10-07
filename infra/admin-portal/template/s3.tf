#
# S3 resources for hosting the Admin Portal website
#

resource "aws_s3_bucket" "admin_portal_web" {
  bucket = "massgov-${local.app_name}-${var.environment_name}-admin-portal-site-builds"
  website {
    index_document = "index.html"
    error_document = "404.html"
  }

  # EOTSS AWS Tagging Standards
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-${local.app_name}-${var.environment_name}-admin-portal-site-builds"
    public      = "yes"
  })
}

data "aws_iam_policy_document" "admin_portal_web" {
  statement {
    sid       = "PublicReadForGetBucketObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.admin_portal_web.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "admin_portal_web_policy" {
  bucket = aws_s3_bucket.admin_portal_web.id
  policy = data.aws_iam_policy_document.admin_portal_web.json
}
