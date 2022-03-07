#------------------------------------------------------------------------------#
#                        Rate-limiting AWS WAF rule                            #
#------------------------------------------------------------------------------#

# Ref:
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl

# Regional API WAF


locals {
  api_gateway_stage_arn  = "arn:aws:apigateway:us-east-1::/restapis/${aws_api_gateway_rest_api.pfml.id}/stages/${var.environment_name}"
  api_gateway_deployment = "aws_api_gateway_deployment.${var.environment_name}"
}

resource "aws_wafv2_web_acl" "regional_api_acl" {
  name  = "mass-pfml-${var.environment_name}-api-acl"
  scope = "REGIONAL"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[local.constants_env]
  })

  default_action {
    allow {}
  }

  #------------------------------------------------------------------------------#
  #                        log4j-ZDE AWS WAF rule                            #
  #------------------------------------------------------------------------------#
  rule {
    name     = "mass-pfml-${var.environment_name}-log4j-ZDE-acl"
    priority = 0


    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"

        excluded_rule {
          name = "Host_localhost_HEADER"
        }

        excluded_rule {
          name = "PROPFIND_METHOD"
        }

        excluded_rule {
          name = "ExploitablePaths_URIPATH"
        }

      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "log4j-ZDE"
      sampled_requests_enabled   = true
    }
  }

  #------------------------------------------------------------------------------#
  #                        Rate-limiting AWS WAF rule                            #
  #------------------------------------------------------------------------------#
  # Default allow unless IP is sending under "limit" requests per 5 minutes.
  rule {
    name     = "mass-pfml-${var.environment_name}-rate-based-acl"
    priority = 1

    dynamic "action" {
      for_each = var.enable_regional_rate_based_acl ? [1] : []
      content {
        block {}
      }
    }

    dynamic "action" {
      for_each = var.enable_regional_rate_based_acl ? [] : [1]
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
      metric_name                = "mass-pfml-${var.environment_name}-rate-limited"
      sampled_requests_enabled   = true
    }
  }

  #------------------------------------------------------------------------------#
  #                            Geo Match AWS WAF rule                            #
  #------------------------------------------------------------------------------#
  rule {
    name     = "massgov-pfml-${var.environment_name}-block-high-risk-countries-rule"
    priority = 2
    action {
      block {}
    }
    statement {
      geo_match_statement {
        country_codes = module.constants.high_risk_country_codes
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "massgov-pfml-${var.environment_name}-block-high-risk-countries"
      sampled_requests_enabled   = true
    }
  }

  #------------------------------------------------------------------------------#
  #                      Fortinet OWASP 10 AWS WAF rule                          #
  #------------------------------------------------------------------------------#
  rule {
    name     = "mass-pfml-${var.environment_name}-fortinet-managed-rules"
    priority = 3

    dynamic "override_action" {
      for_each = var.enforce_fortinet_managed_rules ? [1] : []
      content {
        none {}
      }
    }

    dynamic "override_action" {
      for_each = var.enforce_fortinet_managed_rules ? [] : [1]
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
      metric_name                = "mass-pfml-${var.environment_name}-fortinet-rule-group"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "mass-pfml-${var.environment_name}-rate-monitored"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "rate_based_acl" {
  depends_on = [local.api_gateway_deployment]
  # must be an must be an ARN of an Application Load Balancer or an Amazon API Gateway stage.
  # resource_arn will need to be manually entered prior to
  resource_arn = local.api_gateway_stage_arn
  web_acl_arn  = aws_wafv2_web_acl.regional_api_acl.arn
}