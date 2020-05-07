#
# Terraform configuration for Lambda functions.
#

data "aws_s3_bucket" "lambda_build" {
  bucket = "massgov-pfml-api-lambda-builds"
}

# The DOR Import Function
resource "aws_lambda_function" "dor_import" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = "dor-import/${var.dor_import_lambda_build_s3_key}"

  function_name = "massgov-pfml-${var.environment_name}-dor-import"
  handler       = "import_dor.handler"
  runtime       = var.lambda_runtime
  publish       = "true"

  timeout = 900

  role = aws_iam_role.lambda_role.arn

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
      DB_URL      = aws_db_instance.default.address
      DB_NAME     = aws_db_instance.default.name
      DB_USERNAME = aws_db_instance.default.username
      DB_PASSWORD = aws_ssm_parameter.db_password.value
    }
  }
}
