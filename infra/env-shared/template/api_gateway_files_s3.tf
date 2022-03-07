################################################################
# Utilizes the "endpoints" config to generate API gateway resources
# authorized for S3 operations under the /files endpoint. 
################################################################

# ----------------------------------------------------------------------------------------------------------------------
# API Resources
# ----------------------------------------------------------------------------------------------------------------------

# Root resource under /api
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
