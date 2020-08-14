#
# Terraform configuration for Lambda functions.
#

data "aws_s3_bucket" "lambda_build" {
  bucket = "massgov-pfml-api-lambda-builds"
}

resource "aws_lambda_layer_version" "dependencies" {
  s3_bucket  = data.aws_s3_bucket.lambda_build.bucket
  s3_key     = "dor-import/${var.dor_import_lambda_dependencies_s3_key}"
  layer_name = "massgov-pfml-${var.environment_name}-dor-import-dependencies"
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

  layers = ["${aws_lambda_layer_version.dependencies.arn}"]

  environment {
    variables = {
      DB_HOST                                = aws_db_instance.default.address
      DB_NAME                                = aws_db_instance.default.name
      DB_USERNAME                            = "pfml_api"
      DECRYPT                                = "true"
      GPG_DECRYPTION_KEY_SSM_PATH            = "/service/${local.app_name}-dor-import/${var.environment_name}/gpg_decryption_key"
      GPG_DECRYPTION_KEY_PASSPHRASE_SSM_PATH = "/service/${local.app_name}-dor-import/${var.environment_name}/gpg_decryption_key_passphrase"
      FOLDER_PATH                            = "s3://massgov-pfml-${var.environment_name}-agency-transfer/dor/received"
    }
  }
}

resource "aws_lambda_function_event_invoke_config" "dor_import_invoke_config" {
  function_name                = "massgov-pfml-${var.environment_name}-dor-import"
  maximum_event_age_in_seconds = 21600 # 6 hours
  maximum_retry_attempts       = 2
}

resource "aws_lambda_function" "cognito_post_confirmation" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = var.cognito_post_confirmation_lambda_artifact_s3_key

  # This function is connected to Cognito in the Portal Terrafrom configs via
  # this name, any changes to the function name should be done by deploying a
  # new Lambda function with the updated name, updating the Portal config to
  # point to new Lambda, then drop the old Lambda. Otherwise downtime is
  # required/User creation is broken.
  function_name = "massgov-pfml-${var.environment_name}-cognito_post_confirmation"
  handler       = "handler.handler"
  runtime       = var.lambda_runtime
  publish       = "true"

  # Cognito will only wait 5 seconds, so match that timeout here for
  # consistency.
  timeout = 5

  role = aws_iam_role.lambda_role.arn

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
      DB_HOST     = aws_db_instance.default.address
      DB_NAME     = aws_db_instance.default.name
      DB_USERNAME = "pfml_api"
    }
  }
}

resource "aws_lambda_permission" "allow_cognito_post_confirmation" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_post_confirmation.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito_user_pool_arn
}

resource "aws_lambda_function" "eligibility_feed" {
  s3_bucket = data.aws_s3_bucket.lambda_build.bucket
  s3_key    = "fineos-eligibility-feed-export/${var.fineos_eligibility_transfer_lambda_build_s3_key}"

  function_name = "massgov-pfml-${var.environment_name}-eligibility-feed"
  handler       = "eligibility_export.handler"

  runtime = var.lambda_runtime
  publish = "true"

  timeout = 900

  role = aws_iam_role.lambda_role.arn

  vpc_config {
    subnet_ids         = var.vpc_app_subnet_ids
    security_group_ids = [aws_security_group.data_import.id]
  }

  environment {
    variables = {
      DB_HOST              = aws_db_instance.default.address
      DB_NAME              = aws_db_instance.default.name
      DB_USERNAME          = aws_db_instance.default.username
      DB_PASSWORD_SSM_PATH = "/service/${local.app_name}/${var.environment_name}/db-password"
      # need fineos s3 bucket
      # FOLDER_PATH                            = "s3://massgov-pfml-${var.environment_name}-fineos-transfer"
    }
  }
}