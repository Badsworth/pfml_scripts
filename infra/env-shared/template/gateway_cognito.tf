/*
  Terraform configuration for the creation of API Gateway -> Cognito proxy resources.
  N.B.: The API Gateway URL ('https://paidleave-api-<environment>.mass.gov/api/v1/oauth2/token')
  will be proxied to the corresponding Cognito instance's URL for the environment
  (https://massgov-pfml-<environment>.auth.us-east-1.amazoncognito.com/oauth2/token)

*/

resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "v1"
}

resource "aws_api_gateway_resource" "cognito_oauth2" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "oauth2"
}

resource "aws_api_gateway_resource" "cognito_token" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.cognito_oauth2.id
  path_part   = "token"
}


resource "aws_api_gateway_method" "cognito_token_post" {
  rest_api_id   = aws_api_gateway_rest_api.pfml.id
  resource_id   = aws_api_gateway_resource.cognito_token.id
  http_method   = "POST"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "integration_cognito_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.pfml.id
  resource_id             = aws_api_gateway_resource.cognito_token.id
  http_method             = aws_api_gateway_method.cognito_token_post.http_method
  integration_http_method = "POST"
  type                    = "HTTP_PROXY"
  connection_type         = "INTERNET"
  uri                     = "https://massgov-pfml-${var.environment_name}.auth.us-east-1.amazoncognito.com/oauth2/token"
}
