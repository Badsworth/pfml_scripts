#------------------------------------------------------------------------------#
#                        Rate-limiting AWS WAF rule                            #
#------------------------------------------------------------------------------#

# Ref:
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl

# Regional rate-based rule. This can be attached to the API Gateway
# Default allow unless IP is sending under "limit" requests per 5 minutes.

locals {
  api_gateway_stage_arn  = "arn:aws:apigateway:us-east-1::/restapis/${aws_api_gateway_rest_api.pfml.id}/stages/${var.environment_name}"
  api_gateway_deployment = "aws_api_gateway_deployment.${var.environment_name}"
}

resource "aws_wafv2_web_acl" "regional_rate_based_acl" {
  name  = "mass-pfml-${var.environment_name}-regional-rate-based-acl"
  scope = "REGIONAL"

  # Only apply this ACL if set to true in ../environments/<enviroment_name>/main.tf
  count = var.enable_regional_rate_based_acl ? 1 : 0

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[local.constants_env]
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

# resource "aws_wafv2_web_acl_association" "rate_based_acl" {
#   # Only apply this ACL if set to true in ../environments/<enviroment_name>/main.tf
#   count = var.enable_regional_rate_based_acl ? 1 : 0

#   # must be an must be an ARN of an Application Load Balancer or an Amazon API Gateway stage.
#   # resource_arn will need to be manually entered prior to 
#   resource_arn = aws_api_gateway_stage.pfml.arn
#   web_acl_arn  = aws_wafv2_web_acl.regional_rate_based_acl[0].arn
# }

#------------------------------------------------------------------------------#
#                     Fortinet Managed AWS WAF Rules                           #
#------------------------------------------------------------------------------#


# Ref:
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafregional_web_acl

locals {

  # The Fortinet subscription is procured outside of terraform.
  # To find the regional fortinet rule id use ```$ aws waf-regional list-subscribed-rule-groups```
  # at the command line.
  regional_fortinet_rule_id = "a9ae79c6-5ffa-4758-aca7-5a6862b26fa6"
}

resource "aws_wafregional_web_acl" "fortinet_managed_rules" {
  name        = "mass-pfml-${var.environment_name}-regional-fortinet-acl"
  metric_name = "FortinetAWSAPIGatewayRuleset"

  # Only apply this ACL if set to true in ../environments/<enviroment_name>/main.tf
  count = var.enable_fortinet_managed_rules ? 1 : 0

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[local.constants_env]
  })

  default_action {
    type = "ALLOW"
  }

  logging_configuration {
    log_destination = aws_kinesis_firehose_delivery_stream.aws_waf.arn
  }

  rule {
    priority = 1
    rule_id  = local.regional_fortinet_rule_id
    type     = "GROUP"

    override_action {
      # NONE  = None of the rules in the group will be overriden.
      # COUNT = Count the rules that triggered but do not block.
      type = var.enforce_fortinet_managed_rules ? "NONE" : "COUNT"
    }
  }
}

resource "aws_wafregional_web_acl_association" "api_gateway" {
  count        = var.enable_fortinet_managed_rules ? 1 : 0
  resource_arn = aws_api_gateway_stage.pfml.arn
  web_acl_id   = aws_wafregional_web_acl.fortinet_managed_rules[0].id
}
