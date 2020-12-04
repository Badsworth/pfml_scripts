# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl
# managed and rate based rule examples at the URL above. 

locals {
  api_gateway_arn        = "arn:aws:apigateway:us-east-1::/restapis/${aws_api_gateway_rest_api.pfml.id}/stages/${var.environment_name}"
  api_gateway_deployment = "aws_api_gateway_deployment.${var.environment_name}"
}

# Regional rate-based rule. This can be attached to the API Gateway
# Default allow unless IP is sending under 1,000 requests per 5 minutes.
resource "aws_wafv2_web_acl" "regional_rate_based_acl" {
  name  = "regional-rate-based-acl"
  scope = "REGIONAL"

  # No rate limiting in performance environment for now (4 Dec 2020)
  count = var.environment_name == "performance" ? 0 : 1

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })

  default_action {
    allow {}
  }

  rule {
    name     = "rate_based_acl"
    priority = 0

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 3000 # This is arbitrary until we get some baseline usage data
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "rate-limited"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "rate-monitored"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "rate_based_acl" {
  # No rate limiting in performance environment for now (4 Dec 2020)
  count = var.environment_name == "performance" ? 0 : 1

  depends_on = [local.api_gateway_deployment]
  # must be an must be an ARN of an Application Load Balancer or an Amazon API Gateway stage.
  # resource_arn will need to be manually entered prior to 
  resource_arn = local.api_gateway_arn
  web_acl_arn  = aws_wafv2_web_acl.regional_rate_based_acl[0].arn
}
