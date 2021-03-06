provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

# Cloudfront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "admin_portal_web_origin_access_identity" {
  comment = "PFML Admin Portal (${var.environment_name})"
}

resource "aws_cloudfront_distribution" "admin_portal_web_distribution" {
  # AWS Web Application Firewall
  # If environment is performance, do nothing; else connect the rate-limit firewall
  web_acl_id = aws_wafv2_web_acl.cloudfront_waf_acl.arn

  origin {
    domain_name = aws_s3_bucket.admin_portal_web.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.admin_portal_web.id
    # set as an environment variable during github workflow
    origin_path = var.cloudfront_origin_path
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.admin_portal_web_origin_access_identity.cloudfront_access_identity_path
    }
  }

  logging_config {
    bucket = data.aws_s3_bucket.cloudfront_access_logging.bucket_domain_name
    prefix = var.environment_name
  }

  comment             = "PFML Admin Portal (${var.environment_name})"
  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http2"
  default_root_object = "index.html"
  aliases             = local.domain == null ? null : [local.domain]
  price_class         = "PriceClass_100"
  retain_on_delete    = true
  # Terraform will exit as soon as it’s made all the updates
  # to AWS API objects and won’t poll for the distribution to become ready,
  # which can take 15 to 20 minutes
  wait_for_deployment = false
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = aws_s3_bucket.admin_portal_web.id

    forwarded_values {
      query_string = false
      headers      = ["Origin"]

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

  custom_error_response {
    error_code         = 404
    response_code      = 404
    response_page_path = "/404/index.html"
  }

  viewer_certificate {
    acm_certificate_arn            = local.cert_domain == null ? null : data.aws_acm_certificate.admin_portal_cert_domains[0].arn
    cloudfront_default_certificate = (local.cert_domain == null)

    # SNI is recommended
    # Associates alternate domain names with an IP address for each edge location
    # See: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-https-dedicated-ip-or-sni.html
    ssl_support_method = "sni-only"

    # If we're using cloudfront_default_certificate, TLSv1 must be specified.
    minimum_protocol_version = local.cert_domain == null ? "TLSv1" : "TLSv1.2_2019"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}
