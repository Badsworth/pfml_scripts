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

locals {
  google_tag_manager_snippet_hashes_list = [
    "'sha256-6bOQFA12d94CECGI1FeXqgg7Dnk8aHUxum07Xs/GGbA='", # test
    "'sha256-5lXWtIB9qW9mx6Adr1BrKsJYWjJTZnDhXuZyYJlqQzE='", # stage
    "'sha256-kuMZ4LjimNmsionsNpKxrnz2EzMJj1y/pq75KgD0fzY='", # prod
  ]
  google_tag_manager_snippet_hashes = join(" ", local.google_tag_manager_snippet_hashes_list)
  allowed_google_script_src         = "https://www.googletagmanager.com/ https://www.google-analytics.com/"
  allowed_new_relic_script_src      = "https://js-agent.newrelic.com/ https://bam.nr-data.net/"
  allowed_script_src                = "'self' ${local.allowed_google_script_src} ${local.allowed_new_relic_script_src} ${local.google_tag_manager_snippet_hashes}"
}

resource "aws_cloudfront_response_headers_policy" "portal_response_header_policy" {
  name    = "portal-{var.environment_name}-response-header-policy"
  comment = "Portal response header policy"


  security_headers_config {
    # only allow resource for this domain. keep resources from being loaded over http
    # do not allow base tag
    # do not allow form actions
    # https://infosec.mozilla.org/guidelines/web_security#content-security-policy
    content_security_policy {
      content_security_policy = "default-src 'self' https:; script-src ${local.allowed_script_src}; base-uri 'none'; form-action 'none'; img-src 'self' https://www.google-analytics.com/ blob:"
      override                = true
    }
    # sets nosniff header
    # don't use scripts or stylesheets that don't have the correct MIME
    # type, which prevent browsers from incorrectly detecting non-scripts
    # as scripts, which helps prevent XSS attacks
    # https://infosec.mozilla.org/guidelines/web_security#x-content-type-options
    content_type_options {
      override = true
    }
    # block site being used in an iframe which prevents clickjacking,
    # `frame-ancestors` directive in a CSP is more flexible, but not
    # supported everywhere yet, so this header is a backup for older
    # browsers
    # https://infosec.mozilla.org/guidelines/web_security#x-frame-options
    frame_options {
      frame_option = "DENY"
      override     = true
    }
    # only send shortened `Referrer` header to a non-same site origin, full
    # referrer header to the same origin, this is a privacy measure,
    # protects against leaking (potentially sensitive) information to an
    # external site that may be in a path or query parameter
    # https://infosec.mozilla.org/guidelines/web_security#referrer-policy
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
    # only connect to this site over HTTPS
    # https://infosec.mozilla.org/guidelines/web_security#http-strict-transport-security
    strict_transport_security {
      access_control_max_age_sec = 31536000
      override                   = true
    }

    # in IE/Chrome, block page from loading if a XSS attack is detected,
    # largely unnecessary if a good CSP is in place, but again helps
    # protect older browsers
    # https://infosec.mozilla.org/guidelines/web_security#x-xss-protection
    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }
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

    viewer_protocol_policy     = "redirect-to-https"
    min_ttl                    = 0
    default_ttl                = 31536000
    max_ttl                    = 31536000
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.portal_response_header_policy.id


    lambda_function_association {
      # Executes only when CloudFront forwards a request to S3. When the requested
      # object is in the CloudFront cache, the function doesn’t execute.
      event_type = "origin-request"
      # The Amazon Resource Name (ARN) identifying your Lambda Function Version
      # when publish = true
      lambda_arn = aws_lambda_function.cloudfront_handler.qualified_arn
    }

    # TODO: INFRA-785 
    # # remove this code
    # lambda_function_association {
    #   # The function executes before CloudFront returns the requested object to the viewer.
    #   # The function executes regardless of whether the object was already in the edge cache.
    #   # If the origin returns an HTTP status code other than HTTP 200 (OK), the function doesn't execute.
    #   event_type = "viewer-response"
    #   # The Amazon Resource Name (ARN) identifying your Lambda Function Version
    #   # when publish = true
    #   lambda_arn = aws_lambda_function.cloudfront_handler.qualified_arn
    # }
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
