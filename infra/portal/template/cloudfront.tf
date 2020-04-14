provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

resource "aws_cloudfront_distribution" "portal_web_distribution" {
  origin {
    domain_name = aws_s3_bucket.portal_web.website_endpoint
    origin_id   = aws_s3_bucket.portal_web.id
    # set as an environment variable during github workflow
    origin_path = var.cloudfront_origin_path

    custom_origin_config {
      http_port  = 80
      https_port = 443
      # this must be http-only because AWS doesn't support HTTPS for S3 website
      # endpoints, see
      # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesOriginProtocolPolicy
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http2"
  default_root_object = "index.html"
  aliases             = var.domain == "" ? [] : [var.domain]
  price_class         = "PriceClass_100"
  retain_on_delete    = true

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = aws_s3_bucket.portal_web.id

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
    response_page_path = "/404.html"
  }

  viewer_certificate {
    acm_certificate_arn            = var.cloudfront_certificate_arn
    cloudfront_default_certificate = (var.cloudfront_certificate_arn == null)

    ssl_support_method = "sni-only"
    # TODO: we might need to use TLSv1.1_2016 for broader compatibility
    minimum_protocol_version = "TLSv1.2_2018"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}
