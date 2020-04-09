locals {
  domain = var.domain != "" ? var.domain : "pfml-${var.environment_name}.${var.tld}"
}

provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

data "aws_acm_certificate" "domain" {
  # ACM certs have to be in us-east-1 to be used with CloudFront
  provider = aws.us-east-1

  # you cannot lookup certs by a SAN, so we lookup based on the TLD with the
  # assumption it also has a wildcard cert as a SAN
  domain      = var.tld
  statuses    = ["ISSUED"]
  most_recent = true
}

# CDN

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
  aliases             = [local.domain]
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
    acm_certificate_arn = data.aws_acm_certificate.domain.arn

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

# DNS

data "aws_route53_zone" "tld" {
  name = var.tld
}

resource "aws_route53_record" "root_v4" {
  zone_id = data.aws_route53_zone.tld.zone_id
  name    = local.domain
  type    = "A"

  alias {
    name    = aws_cloudfront_distribution.portal_web_distribution.domain_name
    zone_id = aws_cloudfront_distribution.portal_web_distribution.hosted_zone_id

    evaluate_target_health = false
  }
}

resource "aws_route53_record" "root_v6" {
  zone_id = data.aws_route53_zone.tld.zone_id
  name    = local.domain
  type    = "AAAA"

  alias {
    name    = aws_cloudfront_distribution.portal_web_distribution.domain_name
    zone_id = aws_cloudfront_distribution.portal_web_distribution.hosted_zone_id

    evaluate_target_health = false
  }
}
