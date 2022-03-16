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
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.namespace[each.key].id
  path_part   = "{key+}"
}

# /files/<namespace>/list
resource "aws_api_gateway_resource" "files_list" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.namespace[each.key].id
  path_part   = "list"
}

# /files/<namespace>/list/{relative_object_key}
resource "aws_api_gateway_resource" "files_list_key" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.files_list[each.key].id
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
    throttle {
      burst_limit = 10
      path        = "/files/list/${each.value.resource_name}/{key+}/GET"
      rate_limit  = 100
    }
    throttle {
      burst_limit = 10
      path        = "/files/${each.value.resource_name}/{key+}/DELETE"
      rate_limit  = 100
    }
    throttle {
      burst_limit = 10
      path        = "/files/${each.value.resource_name}/{key+}/GET"
      rate_limit  = 100
    }
    throttle {
      burst_limit = 10
      path        = "/files/${each.value.resource_name}/{key+}/PUT"
      rate_limit  = 100
    }
  }

  quota_settings {
    limit  = 10000
    offset = 0
    period = "DAY"
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
# GET list/{bucket}/{key} endpoint to proxy S3 ListObjectsV2
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_api_gateway_method" "files_list_objects_method" {
  for_each         = local.endpoints
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.files_list_key[each.key].id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.key"                 = true
    "method.request.querystring.max_keys"     = false
    "method.request.querystring.start_after"  = false
    "method.request.querystring.no_slash_fix" = false
  }
}

resource "aws_api_gateway_method_response" "files_list_objects_response_200" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.files_list_key[each.key].id
  http_method = aws_api_gateway_method.files_list_objects_method[each.key].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Timestamp"      = true
    "method.response.header.Content-Length" = true
    "method.response.header.Content-Type"   = true
  }
}

resource "aws_api_gateway_method_response" "files_list_objects_response_403" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.files_list_key[each.key].id
  http_method = aws_api_gateway_method.files_list_objects_method[each.key].http_method
  status_code = "403"

  response_parameters = {
    "method.response.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "files_list_objects_s3_integration" {
  for_each    = local.endpoints
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.files_list_key[each.key].id
  http_method = aws_api_gateway_method.files_list_objects_method[each.key].http_method

  type                    = "AWS"
  integration_http_method = "GET"

  uri         = "arn:aws:apigateway:us-east-1:s3:path/${each.value.bucket}/${each.value.object_prefix}{key}"
  credentials = aws_iam_role.files_executor_role[each.key].arn

  request_parameters = {
    "integration.request.querystring.list-type"   = "'2'"
    "integration.request.querystring.delimiter"   = "'/'"
    "integration.request.querystring.max-keys"    = "method.request.querystring.max_keys"
    "integration.request.querystring.start-after" = "method.request.querystring.start_after"
  }

  request_templates = {
    "application/json" : <<EOD
#set($bucketKey="$util.urlDecode($input.params('key'))")
#set($shouldFixSlash= !$bucketKey.endsWith('/') && "$input.params('no_slash_fix')" == "" )
#if( $shouldFixSlash )
  #set($bucketKey="$bucketKey/")
#end
#set($context.requestOverride.querystring.prefix="$bucketKey")
EOD
  }
}

resource "aws_api_gateway_integration_response" "files_list_objects_s3_integration_response_200" {
  for_each          = local.endpoints
  depends_on        = [aws_api_gateway_integration.files_list_objects_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.files_list_key[each.key].id
  http_method       = aws_api_gateway_method.files_list_objects_method[each.key].http_method
  status_code       = "200"
  selection_pattern = "200"

  response_parameters = {
    "method.response.header.Timestamp"      = "integration.response.header.Date"
    "method.response.header.Content-Length" = "integration.response.header.Content-Length"
    "method.response.header.Content-Type"   = "integration.response.header.Content-Type"
  }
}

resource "aws_api_gateway_integration_response" "files_list_objects_s3_integration__response_403" {
  for_each          = local.endpoints
  depends_on        = [aws_api_gateway_integration.files_list_objects_s3_integration]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.files_list_key[each.key].id
  http_method       = aws_api_gateway_method.files_list_objects_method[each.key].http_method
  status_code       = "403"
  selection_pattern = "403"

  response_parameters = {
    "method.response.header.Content-Type" = "integration.response.header.Content-Type"
  }
}