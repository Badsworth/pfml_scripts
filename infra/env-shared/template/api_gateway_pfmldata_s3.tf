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
