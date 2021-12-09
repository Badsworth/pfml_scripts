#------------------------------------------------------------------------------#
#                           CloudFront AWS WAF ACL                             #
#------------------------------------------------------------------------------#

locals {
  kinesis_data_firehose_arn = "arn:aws:firehose:us-east-1:498823821309:deliverystream/aws-waf-logs-${var.environment_name}-kinesis-to-s3"
}

resource "aws_wafv2_web_acl" "cloudfront_waf_acl" {
  name  = "mass-${local.app_name}-${var.environment_name}-cloudfront-admin-acl"
  scope = "CLOUDFRONT"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })

  default_action {
    block {}
  }

  #------------------------------------------------------------------------------#
  #                        IP Whitelist AWS WAF rule                            #
  #------------------------------------------------------------------------------#
  rule {
    name     = "mass-${local.app_name}-${var.environment_name}-ip-whitelist-acl"
    priority = 0

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.workspaces_ip_whitelist.arn
        ip_set_forwarded_ip_config {
          fallback_behavior = "NO_MATCH"
          header_name       = "X-Forwarded-For"
          position          = "ANY"
        }
      }
    }

    action {
      allow {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "mass-${local.app_name}-${var.environment_name}-ip-whitelist-metric"
      sampled_requests_enabled   = true
    }
  }

  #------------------------------------------------------------------------------#
  #                        Rate-limiting AWS WAF rule                            #
  #------------------------------------------------------------------------------#
  rule {
    name     = "mass-${local.app_name}-${var.environment_name}-rate-based-acl"
    priority = 1

    dynamic "action" {
      for_each = var.enforce_cloudfront_rate_limit ? [1] : []
      content {
        block {}
      }
    }

    dynamic "action" {
      for_each = var.enforce_cloudfront_rate_limit ? [] : [1]
      content {
        count {}
      }
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "mass-${local.app_name}-${var.environment_name}-rate-limited"
      sampled_requests_enabled   = true
    }
  }
  #------------------------------------------------------------------------------#
  #                      Fortinet OWASP 10 AWS WAF rule                          #
  #------------------------------------------------------------------------------#
  rule {
    name     = "mass-${local.app_name}-${var.environment_name}-fortinet-managed-rules"
    priority = 2


    dynamic "override_action" {
      for_each = var.enforce_cloudfront_fortinet_rules ? [1] : []
      content {
        none {}
      }
    }

    dynamic "override_action" {
      for_each = var.enforce_cloudfront_fortinet_rules ? [] : [1]
      content {
        count {}
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "all_rules"
        vendor_name = "Fortinet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "mass-${local.app_name}-${var.environment_name}-fortinet-rule-group"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "mass-${local.app_name}-${var.environment_name}-cloudfront-acl"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_ip_set" "workspaces_ip_whitelist" {
  name               = "mass-${local.app_name}-${var.environment_name}-ip-set"
  description        = "IP Set for AWS Workspaces access to Admin Portal"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses = [
    "10.206.0.0/21",  # LWD 
    "10.203.236.0/24" # PFML
  ]
}

#------------------------------------------------------------------------------#
#                 Kinesis Data Firehose Logging Configuration                  #
#------------------------------------------------------------------------------#

resource "aws_wafv2_web_acl_logging_configuration" "cloudfront_acl" {
  depends_on              = [aws_wafv2_web_acl.cloudfront_waf_acl]
  log_destination_configs = [local.kinesis_data_firehose_arn]
  resource_arn            = aws_wafv2_web_acl.cloudfront_waf_acl.arn
}
