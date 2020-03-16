# Terraform configuration for an API Gateway deployment.
#
# We create one of these per VPC to simplify configuration. Otherwise,
# we'd be linking a central API Gateway config to many different gateway
# deployments/integrations.
#
resource "aws_api_gateway_rest_api" "pfml" {
  name        = "pfml-gateway-${var.environment_name}"
  description = "API Gateway for PFML ${var.environment_name}"
}

resource "aws_api_gateway_deployment" "stage" {
  stage_name  = var.environment_name
  rest_api_id = aws_api_gateway_rest_api.pfml.id

  # A deployment requires at least one integration; we'll require
  # all of them to avoid any confusion with what's been deployed.
  depends_on = [
    aws_api_gateway_integration.integration_api_proxy,
    aws_api_gateway_integration.integration_ui,
    aws_api_gateway_integration.integration_ui_proxy
  ]
}

resource "aws_api_gateway_base_path_mapping" "stage_mapping" {
  stage_name  = var.environment_name
  api_id      = aws_api_gateway_rest_api.pfml.id
  domain_name = aws_api_gateway_domain_name.domain_name.domain_name
}
