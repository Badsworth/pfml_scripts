# ----------------------------------------------------------------------------------------------------------------------
# API Resources
# ----------------------------------------------------------------------------------------------------------------------
resource "aws_api_gateway_resource" "pfmldata" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_rest_api.pfml.root_resource_id
  path_part   = "pfmldata"
}

resource "aws_api_gateway_resource" "pfmldata_bucket" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.pfmldata.id
  path_part   = "{bucket}"
}

resource "aws_api_gateway_resource" "pfmldata_bucket_key" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.pfmldata_bucket.id
  path_part   = "{key+}"
}

resource "aws_api_gateway_resource" "pfmldata_list" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.pfmldata.id
  path_part   = "list"
}

resource "aws_api_gateway_resource" "pfmldata_list_bucket" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.pfmldata_list.id
  path_part   = "{bucket}"
}

resource "aws_api_gateway_resource" "pfmldata_list_bucket_key" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.pfmldata_list_bucket.id
  path_part   = "{key+}"
}

resource "aws_api_gateway_usage_plan" "pfmldata_plan" {
  name        = "pfmldata plan ${var.environment_name}"
  description = "Usage Plan for system (PowerAutomate) accessing files from S3"

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

resource "aws_api_gateway_api_key" "pfmldata_api_key" {
  name = "pfmldata_api_key_${var.environment_name}"
}

resource "aws_api_gateway_usage_plan_key" "pfmldata_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.pfmldata_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.pfmldata_plan.id
}

# ----------------------------------------------------------------------------------------------------------------------
# GET /{bucket}/{key} endpoint to proxy S3 GetObject
# ----------------------------------------------------------------------------------------------------------------------


resource "aws_api_gateway_method" "pfmldata_get_object_method" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.bucket" = true
    "method.request.path.key"    = true
  }
}

resource "aws_api_gateway_method_response" "pfmldata_get_object_response_200" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_get_object_method.http_method
  status_code = "200"
}

resource "aws_api_gateway_method_response" "pfmldata_get_object_response_403" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_get_object_method.http_method
  status_code = "403"
}


resource "aws_api_gateway_integration" "pfmldata_get_object_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_get_object_method.http_method

  integration_http_method = "GET"
  type                    = "AWS"

  uri         = "arn:aws:apigateway:us-east-1:s3:path/{bucket}/{key}"
  credentials = aws_iam_role.pfmldata_executor_role.arn
  request_parameters = {
    "integration.request.path.bucket" : "method.request.path.bucket"
    "integration.request.path.key" : "method.request.path.key"
  }
}

resource "aws_api_gateway_integration_response" "pfmldata_get_object_s3_integration_response_200" {
  depends_on        = [aws_api_gateway_integration.pfmldata_get_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_get_object_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_get_object_response_200.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_get_object_response_200.status_code
}

resource "aws_api_gateway_integration_response" "pfmldata_get_object_s3_integration_response_403" {
  depends_on        = [aws_api_gateway_integration.pfmldata_get_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_get_object_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_get_object_response_403.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_get_object_response_403.status_code
}
