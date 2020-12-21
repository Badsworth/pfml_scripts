# Terraform configuration for an API Gateway deployment.
#
# We create one of these per VPC to simplify configuration. Otherwise,
# we'd be linking a central API Gateway config to many different gateway
# deployments/integrations.
#
resource "aws_api_gateway_rest_api" "pfml" {
  name        = "pfml-gateway-${var.environment_name}"
  description = "API Gateway for PFML ${var.environment_name}"
  binary_media_types = [
    "multipart/form-data",
    "application/pdf",
    "image/jpg",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/heic"
  ]

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_api_gateway_deployment" "stage" {
  stage_name  = var.environment_name
  rest_api_id = aws_api_gateway_rest_api.pfml.id

  triggers = {
    always_run = sha1(timestamp())
  }

  lifecycle {
    create_before_destroy = true
  }

  # A deployment requires at least one integration; we'll require
  # all of them to avoid any confusion with what's been deployed.
  depends_on = [
    aws_api_gateway_integration.integration_api_proxy,
    aws_api_gateway_integration.integration_ui,
    aws_api_gateway_integration.integration_ui_proxy
  ]
}
