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

# ----------------------------------------------------------------------------------------------------------------------
# DELETE /{bucket}/{key+} endpoint to proxy S3 DeleteObject
# ----------------------------------------------------------------------------------------------------------------------


resource "aws_api_gateway_method" "pfmldata_delete_object_method" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method      = "DELETE"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.bucket" = true
    "method.request.path.key"    = true
  }
}

resource "aws_api_gateway_method_response" "pfmldata_delete_object_response_204" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_delete_object_method.http_method
  status_code = "204"
  response_parameters = {
    "method.response.header.Content-Type" = false
  }
}

resource "aws_api_gateway_method_response" "pfmldata_delete_object_response_403" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_delete_object_method.http_method
  status_code = "403"
  response_parameters = {
    "method.response.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "pfmldata_delete_object_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_delete_object_method.http_method

  integration_http_method = "DELETE"
  type                    = "AWS"

  uri         = "arn:aws:apigateway:us-east-1:s3:path/{bucket}/{key}"
  credentials = aws_iam_role.pfmldata_executor_role.arn
  request_parameters = {
    "integration.request.path.bucket" = "method.request.path.bucket"
    "integration.request.path.key"    = "method.request.path.key"
  }
}
resource "aws_api_gateway_integration_response" "pfmldata_delete_object_s3_integration_response_204" {
  depends_on        = [aws_api_gateway_integration.pfmldata_delete_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_delete_object_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_delete_object_response_204.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_delete_object_response_204.status_code
}

resource "aws_api_gateway_integration_response" "pfmldata_delete_object_s3_integration_response_403" {
  depends_on        = [aws_api_gateway_integration.pfmldata_delete_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_delete_object_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_delete_object_response_403.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_delete_object_response_403.status_code
  response_parameters = {
    "method.response.header.Content-Type" = "integration.response.header.Content-Type"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# GET list/{bucket}/{key} endpoint to proxy S3 ListObjectsV2
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_api_gateway_method" "pfmldata_list_objects_method" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.pfmldata_list_bucket_key.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.bucket"             = true
    "method.request.path.key"                = true
    "method.request.querystring.max_keys"    = false
    "method.request.querystring.start_after" = false
  }
}

resource "aws_api_gateway_method_response" "pfmldata_list_objects_response_200" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_list_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_list_objects_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Timestamp"      = true
    "method.response.header.Content-Length" = true
    "method.response.header.Content-Type"   = true
  }
}

resource "aws_api_gateway_method_response" "pfmldata_list_objects_response_403" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_list_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_list_objects_method.http_method
  status_code = "403"

  response_parameters = {
    "method.response.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "pfmldata_list_objects_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_list_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_list_objects_method.http_method

  type                    = "AWS"
  integration_http_method = "GET"

  uri         = "arn:aws:apigateway:us-east-1:s3:path/{bucket}/"
  credentials = aws_iam_role.pfmldata_executor_role.arn

  request_parameters = {
    "integration.request.path.bucket"             = "method.request.path.bucket"
    "integration.request.querystring.list-type"   = "'2'"
    "integration.request.querystring.delimiter"   = "'/'"
    "integration.request.querystring.max-keys"    = "method.request.querystring.max_keys"
    "integration.request.querystring.start-after" = "method.request.querystring.start_after"
  }

  request_templates = {
    "application/json" : <<EOD
{
  #set($context.requestOverride.querystring.prefix="$input.params('key')/")
}
EOD
  }
}

resource "aws_api_gateway_integration_response" "pfmldata_list_objects_s3_integration_response_200" {
  depends_on        = [aws_api_gateway_integration.pfmldata_list_objects_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_list_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_list_objects_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_list_objects_response_200.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_list_objects_response_200.status_code

  response_parameters = {
    "method.response.header.Timestamp"      = "integration.response.header.Date"
    "method.response.header.Content-Length" = "integration.response.header.Content-Length"
    "method.response.header.Content-Type"   = "integration.response.header.Content-Type"
  }
}

resource "aws_api_gateway_integration_response" "pfmldata_list_objects_s3_integration__response_403" {
  depends_on        = [aws_api_gateway_integration.pfmldata_list_objects_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_list_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_list_objects_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_list_objects_response_403.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_list_objects_response_403.status_code

  response_parameters = {
    "method.response.header.Content-Type" = "integration.response.header.Content-Type"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# PUT /{bucket}/{key} endpoint to proxy S3 CopyObject
# ----------------------------------------------------------------------------------------------------------------------
resource "aws_api_gateway_method" "pfmldata_copy_object_method" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method      = "PUT"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.bucket"     = true
    "method.request.path.key"        = true
    "method.request.querystring.src" = true
  }
}

resource "aws_api_gateway_method_response" "pfmldata_copy_object_response_200" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_copy_object_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Timestamp"      = true
    "method.response.header.Content-Length" = true
    "method.response.header.Content-Type"   = true
  }
}

resource "aws_api_gateway_method_response" "pfmldata_copy_object_response_403" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_copy_object_method.http_method
  status_code = "403"

  response_parameters = {
    "method.response.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "pfmldata_copy_object_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method = aws_api_gateway_method.pfmldata_copy_object_method.http_method

  integration_http_method = "PUT"
  type                    = "AWS"

  uri         = "arn:aws:apigateway:us-east-1:s3:path/{bucket}/{key}"
  credentials = aws_iam_role.pfmldata_executor_role.arn
  request_parameters = {
    "integration.request.path.bucket" : "method.request.path.bucket"
    "integration.request.path.key" : "method.request.path.key"
  }

  request_templates = {
    "application/json" : <<EOD
#set($context.requestOverride.header.x-amz-copy-source="$input.params('bucket')/$input.params('src')")
EOD
  }
}

resource "aws_api_gateway_integration_response" "pfmldata_copy_object_s3_integration_response_200" {
  depends_on        = [aws_api_gateway_integration.pfmldata_copy_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_copy_object_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_copy_object_response_200.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_copy_object_response_200.status_code

  response_parameters = {
    "method.response.header.Timestamp"      = "integration.response.header.Date"
    "method.response.header.Content-Length" = "integration.response.header.Content-Length"
    "method.response.header.Content-Type"   = "integration.response.header.Content-Type"
  }
}

resource "aws_api_gateway_integration_response" "pfmldata_copy_object_s3_integration_response_403" {
  depends_on        = [aws_api_gateway_integration.pfmldata_copy_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.pfmldata_bucket_key.id
  http_method       = aws_api_gateway_method.pfmldata_copy_object_method.http_method
  status_code       = aws_api_gateway_method_response.pfmldata_copy_object_response_403.status_code
  selection_pattern = aws_api_gateway_method_response.pfmldata_copy_object_response_403.status_code

  response_parameters = {
    "method.response.header.Content-Type" = "integration.response.header.Content-Type"
  }
}
