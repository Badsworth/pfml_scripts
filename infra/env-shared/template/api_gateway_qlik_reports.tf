# INFRA-794
# TODO: rename as qlik reporting

resource "aws_api_gateway_resource" "business_intellegence" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_rest_api.pfml.root_resource_id
  path_part   = "business_intelligence"

}

resource "aws_api_gateway_resource" "business_intelligence_file" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.business_intellegence.id
  path_part   = "{file+}"
}

resource "aws_api_gateway_usage_plan" "business_intelligence_usage_plan" {
  name        = "qlik plan"
  description = "Usage Plan for system (PowerAutomate) accessing Qlik Reporting API"

  api_stages {
    api_id = aws_api_gateway_rest_api.pfml.id
    stage  = aws_api_gateway_deployment.stage.stage_name
  }

  quota_settings {
    limit  = 10000
    offset = 0
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 10
    rate_limit  = 100
  }
}

resource "aws_api_gateway_api_key" "business_intellegence_automate_key" {
  name = "bi_key"
}

resource "aws_api_gateway_usage_plan_key" "business_intellegence_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.business_intellegence_automate_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.business_intelligence_usage_plan.id

}

resource "aws_api_gateway_method" "business_intelligence_get" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.business_intelligence_file.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.file" = true
  }
}

resource "aws_api_gateway_integration" "s3_integration_get_business_intelligence" {
  depends_on  = [aws_api_gateway_method.business_intelligence_get]
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_get.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "GET"

  type = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:us-east-1:s3:path/${aws_s3_bucket.pfml_reports.bucket}/dfml-qlikdownloads/{file}"
  credentials = aws_iam_role.qlikdata_executor_role.arn

  request_parameters = {
    "integration.request.path.file" = "method.request.path.file"
  }
}

resource "aws_api_gateway_integration_response" "business_intelligence_get_response" {
  depends_on        = [aws_api_gateway_integration.s3_integration_get_business_intelligence]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.business_intelligence_file.id
  http_method       = aws_api_gateway_method.business_intelligence_get.http_method
  status_code       = aws_api_gateway_method_response.business_intelligence_get_response.status_code
  selection_pattern = aws_api_gateway_method_response.business_intelligence_get_response.status_code

  response_parameters = {
    "method.response.header.Content-Type" = "'text/csv'" # AWS console wants single quotes
  }
}

resource "aws_api_gateway_integration_response" "business_intelligence_get_response_403" {
  depends_on        = [aws_api_gateway_integration.s3_integration_get_business_intelligence]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.business_intelligence_file.id
  http_method       = aws_api_gateway_method.business_intelligence_get.http_method
  status_code       = aws_api_gateway_method_response.business_intelligence_get_response_403.status_code
  selection_pattern = aws_api_gateway_method_response.business_intelligence_get_response_403.status_code
}

resource "aws_api_gateway_method_response" "business_intelligence_get_response" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_method_response" "business_intelligence_get_response_403" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_get.http_method
  status_code = "403"
}

# ----------------------------------------------------------------------------------
resource "aws_api_gateway_method" "business_intelligence_put" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.business_intelligence_file.id
  http_method      = "PUT"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.file" = true
  }
}

resource "aws_api_gateway_integration" "s3_integration_put_business_intelligence" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_put.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "PUT"

  type = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:us-east-1:s3:path/${aws_s3_bucket.pfml_reports.bucket}/dfml-qlikuploads/{file}"
  credentials = aws_iam_role.qlikdata_executor_role.arn

  request_parameters = {
    "integration.request.path.file" = "method.request.path.file"
  }
}

# Defines any adjustments made to the response from the api_gateway_integration above: status codes, Content-Types, etc.
resource "aws_api_gateway_integration_response" "business_intelligence_put_response" {
  depends_on        = [aws_api_gateway_integration.s3_integration_put_business_intelligence]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.business_intelligence_file.id
  http_method       = aws_api_gateway_method.business_intelligence_put.http_method
  status_code       = aws_api_gateway_method_response.business_intelligence_put_response.status_code
  selection_pattern = aws_api_gateway_method_response.business_intelligence_put_response.status_code
}

# Defines which segments of the api_gateway_integration_response to return to the original caller of this API endpoint.
resource "aws_api_gateway_method_response" "business_intelligence_put_response" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_put.http_method
  status_code = "200"
}

# ----------------------------------------------------------------------------------------------------------------------

# Defines the presence of a raw HTTP method without routing or response logic. The resources below handle all of that.
resource "aws_api_gateway_method" "business_intelligence_delete" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.business_intelligence_file.id
  http_method      = "DELETE"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.file" = true
  }
}

# Defines the AWS service, or external HTTP endpoint, that the api_gateway_method above routes inbound requests towards.
# There's a lot of magic here. An integration with S3 translates roughly to "do RESTful actions on data stored in S3".
resource "aws_api_gateway_integration" "s3_integration_delete_business_intelligence" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_delete.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "DELETE"

  type = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:us-east-1:s3:path/${aws_s3_bucket.pfml_reports.bucket}/dfml-qlikdownloads/{file}"
  credentials = aws_iam_role.qlikdata_executor_role.arn

  request_parameters = {
    "integration.request.path.file" = "method.request.path.file"
  }
}

# Defines any adjustments made to the response from the api_gateway_integration above: status codes, Content-Types, etc.
resource "aws_api_gateway_integration_response" "business_intelligence_delete_response" {
  depends_on = [aws_api_gateway_integration.s3_integration_delete_business_intelligence]

  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.business_intelligence_file.id
  http_method       = aws_api_gateway_method.business_intelligence_delete.http_method
  status_code       = aws_api_gateway_method_response.business_intelligence_delete_response.status_code
  selection_pattern = aws_api_gateway_method_response.business_intelligence_delete_response.status_code
}

# Defines which segments of the api_gateway_integration_response to return to the original caller of this API endpoint.
resource "aws_api_gateway_method_response" "business_intelligence_delete_response" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.business_intelligence_file.id
  http_method = aws_api_gateway_method.business_intelligence_delete.http_method
  status_code = "204"
}
