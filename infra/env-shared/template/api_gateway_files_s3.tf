################################################################
# Utilizes the "endpoints" config to generate API gateway resources
# authorized for S3 operations under the /files endpoint. 
################################################################

# ----------------------------------------------------------------------------------------------------------------------
# API Resources
# ----------------------------------------------------------------------------------------------------------------------

# Root resource under /
resource "aws_api_gateway_resource" "files" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_rest_api.pfml.root_resource_id
  path_part   = "files"
}

# Generate resources for each named endpoint under /files
resource "aws_api_gateway_resource" "namespace" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.files.id
  path_part   = each.value.resource_name
}

# /files/<namespace>/{relative_object_key}
resource "aws_api_gateway_resource" "files_key" {
  for_each    = aws_api_gateway_resource.namespace
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = each.value.id
  path_part   = "{key+}"
}

# /files/<namespace>/list
resource "aws_api_gateway_resource" "files_list" {
  for_each    = aws_api_gateway_resource.namespace
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = each.value.id
  path_part   = "list"
}

# /files/<namespace>/list/{relative_object_key}
resource "aws_api_gateway_resource" "files_list_key" {
  for_each    = aws_api_gateway_resource.files_list
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = each.value.id
  path_part   = "{key+}"
}


# ----------------------------------------------------------------------------------------------------------------------
# Usage Plan
# ----------------------------------------------------------------------------------------------------------------------

# Each use case has a quota that restricts use of other api resources
resource "aws_api_gateway_usage_plan" "files_usage_plan" {
  for_each    = local.endpoints
  name        = "massgov-pfml-${var.environment_name}-${each.key}-usage-plan"
  description = "Usage plan set for ${each.key} to access files from S3"
  api_stages {
    api_id = aws_api_gateway_rest_api.pfml.id
    stage  = aws_api_gateway_deployment.stage.stage_name

    # By default access is restricted on all endpoints
    throttle {
      burst_limit = 0
      path        = "*/*"
      rate_limit  = 0
    }
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

# API key specific to each use case
resource "aws_api_gateway_api_key" "files_api_key" {
  for_each = local.endpoints
  name     = "massgov-pfml-${var.environment_name}-${each.key}-api-key"
}

# Associate the api key with the usage plan
resource "aws_api_gateway_usage_plan_key" "files_usage_plan_key" {
  for_each      = local.endpoints
  key_id        = aws_api_gateway_api_key.files_api_key[each.key].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.files_usage_plan[each.key].id
}


# ----------------------------------------------------------------------------------------------------------------------
# DELETE /{bucket}/{key+} endpoint to proxy S3 DeleteObject
# ----------------------------------------------------------------------------------------------------------------------


resource "aws_api_gateway_method" "files_delete_object_method" {
  for_each         = local.endpoints
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.files_key[each.key].id
  http_method      = "DELETE"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.key" = true
  }
}

resource "aws_api_gateway_method_response" "files_delete_object_response_204" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.files_key[each.key].id
  http_method = aws_api_gateway_method.files_delete_object_method[each.key].http_method
  status_code = "204"
  response_parameters = {
    "method.response.header.Content-Type" = false
  }
}

resource "aws_api_gateway_method_response" "files_delete_object_response_403" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.files_key[each.key].id
  http_method = aws_api_gateway_method.files_delete_object_method[each.key].http_method
  status_code = "403"
  response_parameters = {
    "method.response.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "files_delete_object_s3_integration" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.files_key[each.key].id
  http_method = aws_api_gateway_method.files_delete_object_method[each.key].http_method

  integration_http_method = "DELETE"
  type                    = "AWS"

  uri         = "arn:aws:apigateway:us-east-1:s3:path/${each.value.bucket.id}/${each.value.object_prefix}{key}"
  credentials = aws_iam_role.files_executor_role[each.key].arn
  request_parameters = {
    "integration.request.path.key" = "method.request.path.key"
  }
}
resource "aws_api_gateway_integration_response" "files_delete_object_s3_integration_response_204" {
  for_each          = local.endpoints
  depends_on        = [aws_api_gateway_integration.files_delete_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.files_key[each.key].id
  http_method       = aws_api_gateway_method.files_delete_object_method[each.key].http_method
  status_code       = "204"
  selection_pattern = "204"
}

resource "aws_api_gateway_integration_response" "files_delete_object_s3_integration_response_403" {
  for_each          = local.endpoints
  depends_on        = [aws_api_gateway_integration.files_delete_object_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.files_key[each.key].id
  http_method       = aws_api_gateway_method.files_delete_object_method[each.key].http_method
  status_code       = "403"
  selection_pattern = "403"
  response_parameters = {
    "method.response.header.Content-Type" = "integration.response.header.Content-Type"
  }
}
