#
# S3 resources for hosting the Portal website
#

resource "aws_s3_bucket" "portal_web" {
  bucket = "massgov-${local.app_name}-${var.environment_name}-portal-site-builds"
  website {
    index_document = "index.html"
    error_document = "404.html"
  }

  # EOTSS AWS Tagging Standards
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-${local.app_name}-${var.environment_name}-portal-site-builds"
    public      = "yes"
  })
}

data "aws_iam_policy_document" "portal_web" {
  statement {
    sid       = "PublicReadForGetBucketObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.portal_web.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    # only requests from Cloudfront with User-Agent set with this password
    # will be accepted. see https://abridge2devnull.com/posts/2018/01/restricting-access-to-a-cloudfront-s3-website-origin/
    condition {
      test     = "StringEquals"
      variable = "aws:UserAgent"
      values   = [random_password.s3_user_agent_password.result]
    }
  }
}

resource "aws_s3_bucket_policy" "portal_web_policy" {
  bucket = aws_s3_bucket.portal_web.id
  policy = data.aws_iam_policy_document.portal_web.json
}
