################################################################
# Utilizes the "endpoints" config to generate API gateway resources
# authorized for S3 operations under the /files endpoint. 
#
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
