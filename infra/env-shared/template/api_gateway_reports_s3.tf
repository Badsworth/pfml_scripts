# Defines the root segment of a particular URI path.
# A Full URI is composed of many api_gateway_resources: some dynamic, some static. This one is the string 'reports'.
resource "aws_api_gateway_resource" "reports" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_rest_api.pfml.root_resource_id
  path_part   = "reports"
}

# This resource defines the dynamic {file} segment that all the endpoints below work against...
# ...but no endpoints are defined on the 'reports' root; e.g. there's no GET /reports to get an index of all filenames
resource "aws_api_gateway_resource" "reports_file" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  parent_id   = aws_api_gateway_resource.reports.id
  path_part   = "{file+}"
}

# INFRA-364:
resource "aws_api_gateway_usage_plan" "reports_plan" {
  name        = "reports plan"
  description = "Usage Plan for system (PowerAutomate) accessing Reports API"

  api_stages {
    api_id = aws_api_gateway_rest_api.pfml.id
    stage  = aws_api_gateway_deployment.stage.stage_name
  }

  quota_settings {
    limit  = 1000
    offset = 0
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 10
    rate_limit  = 100
  }
}

resource "aws_api_gateway_api_key" "reports_automate_key" {
  name = "reports_key"
}

resource "aws_api_gateway_usage_plan_key" "reports_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.reports_automate_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.reports_plan.id
}

# ----------------------------------------------------------------------------------------------------------------------

# GET reports/:csv -- retrieve one report from S3 by filename -- GET https://paidleave-foo.mass.gov/reports/foobar.csv
# all CSVs this endpoint retrieves are stored at s3://massgov-pfml-foo-reports/dfml-reports


# Defines the presence of a raw HTTP method without routing or response logic. The resources below handle all of that.
resource "aws_api_gateway_method" "reports_get" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.reports_file.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.file" = true
  }
}

# Defines the AWS service, or external HTTP endpoint, that the api_gateway_method above routes inbound requests towards.
# There's a lot of magic here. An integration with S3 translates roughly to "do RESTful actions on data stored in S3".
resource "aws_api_gateway_integration" "s3_integration_get_reports" {
  depends_on  = [aws_api_gateway_method.reports_get]
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_get.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "GET"

  type = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:us-east-1:s3:path/${aws_s3_bucket.pfml_reports.bucket}/dfml-reports/{file}"
  credentials = aws_iam_role.executor.arn

  request_parameters = {
    "integration.request.path.file" = "method.request.path.file"
  }
}

# Defines any adjustments made to the response from the api_gateway_integration above: status codes, Content-Types, etc.
resource "aws_api_gateway_integration_response" "reports_get_response" {
  depends_on        = [aws_api_gateway_integration.s3_integration_get_reports]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.reports_file.id
  http_method       = aws_api_gateway_method.reports_get.http_method
  status_code       = aws_api_gateway_method_response.reports_get_response.status_code
  selection_pattern = aws_api_gateway_method_response.reports_get_response.status_code

  response_parameters = {
    "method.response.header.Content-Type" = "'text/csv'" # AWS console wants single quotes
  }
}

resource "aws_api_gateway_integration_response" "reports_get_response_403" {
  depends_on        = [aws_api_gateway_integration.s3_integration_get_reports]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.reports_file.id
  http_method       = aws_api_gateway_method.reports_get.http_method
  status_code       = aws_api_gateway_method_response.reports_get_response_403.status_code
  selection_pattern = aws_api_gateway_method_response.reports_get_response_403.status_code
}

# Defines which segments of the api_gateway_integration_response to return to the original caller of this API endpoint.

resource "aws_api_gateway_method_response" "reports_get_response" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# A 403 will be returned from S3 for missing files
# if the role does not have access to the list the bucket contents.
resource "aws_api_gateway_method_response" "reports_get_response_403" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_get.http_method
  status_code = "403"
}

# ----------------------------------------------------------------------------------------------------------------------

# PUT reports/:csv -- write one response to S3 by filename -- PUT https://paidleave-foo.mass.gov/reports/foobar.csv
# all CSVs uploaded through this endpoint will be written to s3://massgov-pfml-foo-reports/dfml-responses/
# the CSV to be uploaded should be supplied as base64-encoded utf-8 plaintext, with a Content-Type header of 'text/csv'
# NB: the GET and DELETE endpoints defined in this file don't work on the CSV files uploaded through this endpoint!


# Defines the presence of a raw HTTP method without routing or response logic. The resources below handle all of that.
resource "aws_api_gateway_method" "reports_put" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.reports_file.id
  http_method      = "PUT"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.file" = true
  }
}

# Defines the AWS service, or external HTTP endpoint, that the api_gateway_method above routes inbound requests towards.
# There's a lot of magic here. An integration with S3 translates roughly to "do RESTful actions on data stored in S3".
resource "aws_api_gateway_integration" "s3_integration_put_reports" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_put.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "PUT"

  type = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:us-east-1:s3:path/${aws_s3_bucket.pfml_reports.bucket}/dfml-responses/{file}"
  credentials = aws_iam_role.executor.arn

  request_parameters = {
    "integration.request.path.file" = "method.request.path.file"
  }
}

# Defines any adjustments made to the response from the api_gateway_integration above: status codes, Content-Types, etc.
resource "aws_api_gateway_integration_response" "reports_put_response" {
  depends_on        = [aws_api_gateway_integration.s3_integration_put_reports]
  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.reports_file.id
  http_method       = aws_api_gateway_method.reports_put.http_method
  status_code       = aws_api_gateway_method_response.reports_put_response.status_code
  selection_pattern = aws_api_gateway_method_response.reports_put_response.status_code
}

# Defines which segments of the api_gateway_integration_response to return to the original caller of this API endpoint.
resource "aws_api_gateway_method_response" "reports_put_response" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_put.http_method
  status_code = "200"
}

# ----------------------------------------------------------------------------------------------------------------------

# DELETE reports/:csv -- delete a report from S3 by filename -- DELETE https://paidleave-foo.mass.gov/reports/foobar.csv
# NB: only CSVs uploaded to s3://massgov-pfml-foo-reports/dfml-reports/ can be deleted using this endpoint!


# Defines the presence of a raw HTTP method without routing or response logic. The resources below handle all of that.
resource "aws_api_gateway_method" "reports_delete" {
  rest_api_id      = aws_api_gateway_rest_api.pfml.id
  resource_id      = aws_api_gateway_resource.reports_file.id
  http_method      = "DELETE"
  authorization    = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.file" = true
  }
}

# Defines the AWS service, or external HTTP endpoint, that the api_gateway_method above routes inbound requests towards.
# There's a lot of magic here. An integration with S3 translates roughly to "do RESTful actions on data stored in S3".
resource "aws_api_gateway_integration" "s3_integration_delete_reports" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_delete.http_method

  # Included because of this issue: https://github.com/hashicorp/terraform/issues/10501
  integration_http_method = "DELETE"

  type = "AWS"

  # See uri description: https://docs.aws.amazon.com/apigateway/api-reference/resource/integration/
  uri         = "arn:aws:apigateway:us-east-1:s3:path/${aws_s3_bucket.pfml_reports.bucket}/dfml-reports/{file}"
  credentials = aws_iam_role.executor.arn

  request_parameters = {
    "integration.request.path.file" = "method.request.path.file"
  }
}

# Defines any adjustments made to the response from the api_gateway_integration above: status codes, Content-Types, etc.
resource "aws_api_gateway_integration_response" "reports_delete_response" {
  depends_on = [aws_api_gateway_integration.s3_integration_delete_reports]

  rest_api_id       = aws_api_gateway_rest_api.pfml.id
  resource_id       = aws_api_gateway_resource.reports_file.id
  http_method       = aws_api_gateway_method.reports_delete.http_method
  status_code       = aws_api_gateway_method_response.reports_delete_response.status_code
  selection_pattern = aws_api_gateway_method_response.reports_delete_response.status_code
}

# Defines which segments of the api_gateway_integration_response to return to the original caller of this API endpoint.
resource "aws_api_gateway_method_response" "reports_delete_response" {
  rest_api_id = aws_api_gateway_rest_api.pfml.id
  resource_id = aws_api_gateway_resource.reports_file.id
  http_method = aws_api_gateway_method.reports_delete.http_method
  status_code = "204"
}

# ----------------------------------------------------------------------------------------------------------------------
