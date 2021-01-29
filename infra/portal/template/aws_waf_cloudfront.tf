# CloudFront rate-based rule. This will be attached to a CloudFront distribution
# Default allow unless IP is sending under 1,000 requests per 5 minutes.

locals {
  acl_name = "mass-pfml-${var.environment_name}-cloudfront-rate-based-acl"
}

resource "aws_wafv2_web_acl" "cloudfront_rate_based_acl" {
  name  = local.acl_name
  scope = "CLOUDFRONT"

  # No rate limiting in performance environment for now (4 Dec 2020)
  count = var.environment_name == "performance" ? 0 : 1

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })

  default_action {
    allow {}
  }

  rule {
    name     = "mass-pfml-${var.environment_name}-rate-based-acl"
    priority = 0

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "mass-pfml-${var.environment_name}-rate-limited"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "mass-pfml-${var.environment_name}-rate-monitored"
    sampled_requests_enabled   = true
  }
}
