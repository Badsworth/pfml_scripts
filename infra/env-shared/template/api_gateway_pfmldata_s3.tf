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
