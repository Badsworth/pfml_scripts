# Set up resources to proxy /api/ to the PFML API.
#
resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_rest_api.pfml.root_resource_id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "api_proxy" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "api_proxy_any" {
  rest_api_id   = aws_api_gateway_rest_api.pfml.id
  resource_id   = aws_api_gateway_resource.api_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "integration_api_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.pfml.id
  resource_id             = aws_api_gateway_resource.api_proxy.id
  http_method             = aws_api_gateway_method.api_proxy_any.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = data.aws_api_gateway_vpc_link.vpc_link.id
  uri                     = "http://${data.aws_lb.nlb.dns_name}:${var.nlb_port}/{proxy}"

  request_parameters = {
    "integration.request.path.proxy"              = "method.request.path.proxy"
    "integration.request.header.X-Forwarded-Path" = var.forwarded_path
  }
}
