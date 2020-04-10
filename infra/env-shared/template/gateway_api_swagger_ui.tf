# Terraform configuration for API Gateway --> Swagger UI.
#
# Usually this would be captured under the /api/ proxy integration.
# However, connexion sets up the swagger UI under `/ui/` with a trailing slash,
# and API Gateway implicitly removes trailing slashes from {proxy+} definitions.
#
# Instead, set up a resource for /api/ui/ and /api/ui/{proxy+}. The proxy resource
# provides the Swagger UI with the required CSS and JS bundles.
#
resource "aws_api_gateway_resource" "ui" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "ui"
}

resource "aws_api_gateway_resource" "ui_proxy" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.ui.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "ui_get" {
  rest_api_id   = aws_api_gateway_rest_api.pfml.id
  resource_id   = aws_api_gateway_resource.ui.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "ui_proxy_get" {
  rest_api_id   = aws_api_gateway_rest_api.pfml.id
  resource_id   = aws_api_gateway_resource.ui_proxy.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "integration_ui" {
  rest_api_id             = aws_api_gateway_rest_api.pfml.id
  resource_id             = aws_api_gateway_resource.ui.id
  http_method             = aws_api_gateway_method.ui_get.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = data.aws_api_gateway_vpc_link.vpc_link.id
  uri                     = "http://${data.aws_lb.nlb.dns_name}:${var.nlb_port}/v1/ui/"

  request_parameters = {
    "integration.request.header.X-Forwarded-Path" = "'/api/'"
  }
}

resource "aws_api_gateway_integration" "integration_ui_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.pfml.id
  resource_id             = aws_api_gateway_resource.ui_proxy.id
  http_method             = aws_api_gateway_method.ui_proxy_get.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = data.aws_api_gateway_vpc_link.vpc_link.id
  uri                     = "http://${data.aws_lb.nlb.dns_name}:${var.nlb_port}/v1/ui/{proxy}"

  request_parameters = {
    "integration.request.path.proxy"              = "method.request.path.proxy"
    "integration.request.header.X-Forwarded-Path" = "'/api/'"
  }
}
