#
# S3 and Cloudfront resources for hosting the Storybook website
# which provide tooling for our UI component library and documentation
#

resource "aws_s3_bucket" "storybook" {
  bucket = "massgov-${local.app_name}-${local.environment_name}-storybook-builds"
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
    environment = module.constants.environment_tags[local.environment_name]
    Name        = "massgov-${local.app_name}-${local.environment_name}-storybook-builds"
    public      = "yes"
  })
}

# Block public access
resource "aws_s3_bucket_public_access_block" "storybook" {
  bucket = aws_s3_bucket.storybook.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "storybook" {
  # Visitors will access this site through CloudFront
  statement {
    sid       = "AllowCloudFront"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.storybook.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.storybook_web_origin_access_identity.iam_arn]
    }
  }

  statement {
    sid     = "EnforceTls"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      "${aws_s3_bucket.storybook.arn}/*",
      aws_s3_bucket.storybook.arn
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
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "storybook_policy" {
  bucket = aws_s3_bucket.storybook.id
  policy = data.aws_iam_policy_document.storybook.json
}

# Cloudfront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "storybook_web_origin_access_identity" {
  comment = "PFML Storybook (${local.environment_name})"
}

#CloudFront Distribution
resource "aws_cloudfront_distribution" "storybook_web_distribution" {

  origin {
    domain_name = aws_s3_bucket.storybook.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.storybook.id

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.storybook_web_origin_access_identity.cloudfront_access_identity_path
    }
  }

  comment             = "PFML Storyboard (${local.environment_name})"
  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http2"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  retain_on_delete    = true
  # Terraform will exit as soon as it’s made all the updates
  # to AWS API objects and won’t poll for the distribution to become ready,
  # which can take 15 to 20 minutes
  wait_for_deployment = false
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[local.environment_name]
  })

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = aws_s3_bucket.storybook.id

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 31536000
    max_ttl                = 31536000
    compress               = true

  }

  viewer_certificate {
    cloudfront_default_certificate = true

    # SNI is recommended
    # Associates alternate domain names with an IP address for each edge location
    # See: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-https-dedicated-ip-or-sni.html
    # ssl_support_method = "sni-only"

    # If we're using cloudfront_default_certificate, TLSv1 must be specified.
    minimum_protocol_version = "TLSv1"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

output "storybook_cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.storybook_web_distribution.id
  description = "Cloudfront distribution id for Storybook. Used for cache invalidation in GitHub workflow."
}