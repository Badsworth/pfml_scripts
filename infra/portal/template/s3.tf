resource "aws_s3_bucket" "portal_web" {
  bucket = "massgov-${local.app_name}-${var.environment_name}-portal-site-builds"
  website {
    index_document = "index.html"
    error_document = "404.html"
  }

  # EOTSS AWS Tagging Standards
  tags = {
    secretariat = "eolwd"
    # TODO: Change to DFML once a value exists in the standards
    agency = "eol"
    # TODO: Change to PFML application once a value exists in the standards
    application = "coreinf"

    environment = var.environment_name
    Name        = "massgov-${local.app_name}-${var.environment_name}-portal-site-builds"
    public      = "yes"

    # TODO: Change to business owner once we know
    businessowner = "vijay.rajagopalan2@mass.gov"
    # TODO: Change to mailing list once it exists
    createdby = "sawyer.q.hollenshead@mass.gov"
    # TODO: Change to mailing list once it exists
    itowner = "sawyer.q.hollenshead@mass.gov"
  }
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
      values   = ["${random_password.s3_user_agent_password.result}"]
    }
  }
}

resource "aws_s3_bucket_policy" "portal_web_policy" {
  bucket = aws_s3_bucket.portal_web.id
  policy = data.aws_iam_policy_document.portal_web.json
}
