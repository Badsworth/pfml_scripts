provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

resource "random_password" "s3_user_agent_password" {
  length           = 16
  special          = true
  override_special = "_%@"
  keepers = {
    # Update the date to generate a new password
    date_generated = "2020-04-22"
  }
}

resource "aws_cloudfront_distribution" "portal_web_distribution" {
  # AWS Web Application Firewall
  # If environment is performance, do nothing; else connect the rate-limit firewall
  web_acl_id = aws_wafv2_web_acl.cloudfront_waf_acl.arn

  origin {
    domain_name = aws_s3_bucket.portal_web.website_endpoint
    origin_id   = aws_s3_bucket.portal_web.id
    # set as an environment variable during github workflow
    origin_path = var.cloudfront_origin_path

    # see s3 bucket iam policy
    custom_header {
      name  = "User-Agent"
      value = random_password.s3_user_agent_password.result
    }

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

  comment             = "PFML Claimant Portal (${var.environment_name})"
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

    lambda_function_association {
      # Executes only when CloudFront forwards a request to S3. When the requested
      # object is in the CloudFront cache, the function doesn’t execute.
      event_type = "origin-request"
      # The Amazon Resource Name (ARN) identifying your Lambda Function Version
      # when publish = true
      lambda_arn = aws_lambda_function.cloudfront_handler.qualified_arn
    }

    lambda_function_association {
      # The function executes before CloudFront returns the requested object to the viewer.
      # The function executes regardless of whether the object was already in the edge cache.
      # If the origin returns an HTTP status code other than HTTP 200 (OK), the function doesn't execute.
      event_type = "viewer-response"
      # The Amazon Resource Name (ARN) identifying your Lambda Function Version
      # when publish = true
      lambda_arn = aws_lambda_function.cloudfront_handler.qualified_arn
    }
  }

  custom_error_response {
    error_code         = 404
    response_code      = 404
    response_page_path = "/404/index.html"
  }

  viewer_certificate {
    acm_certificate_arn            = local.cert_domain == null ? null : data.aws_acm_certificate.domain[0].arn
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
