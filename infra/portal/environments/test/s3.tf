#
# S3 resources for hosting the Storybook website
#

resource "aws_s3_bucket" "storybook" {
  bucket = "massgov-${local.app_name}-${local.environment_name}-storybook-builds"
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

    environment = local.environment_name
    Name        = "massgov-${local.app_name}-${local.environment_name}-storybook-builds"
    public      = "yes"

    businessowner = "ma-pfml-alerts@mass.gov"
    createdby     = "ma-pfml-alerts@mass.gov"
    itowner       = "ma-pfml-alerts@mass.gov"
  }
}

data "aws_iam_policy_document" "storybook" {
  # Visitors will access this site directly from the S3 URL
  statement {
    sid       = "PublicReadForGetBucketObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.storybook.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "storybook_policy" {
  bucket = aws_s3_bucket.storybook.id
  policy = data.aws_iam_policy_document.storybook.json
}
