locals {
  # This ARN describes a 3rd-party lambda layer sourced directly from New Relic. It is not managed with Terraform.
  # This layer causes telemetry data to be generated and logged to CloudWatch as a side effect of lambda invocation.
  # Lambda layers are also available for runtimes other than Python 3.8: see https://nr-layers.iopipe.com/.
  newrelic_log_ingestion_layer = "arn:aws:lambda:us-east-1:451483290750:layer:NewRelicPython39:1"
}
data "aws_iam_policy_document" "iam_policy_lambda_assumed_role" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }

  }
}
resource "aws_iam_role" "scrub_ip_lambda_role" {
  name               = "mass-pfml-${var.environment_name}-scrub-ip-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.iam_policy_lambda_assumed_role.json
}
resource "aws_iam_role_policy_attachment" "lambda_basic_executor" {
  role = aws_iam_role.scrub_ip_lambda_role.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda that censors ip addresses
resource "aws_lambda_function" "scrub_ip_addresses_lambda" {
  description      = "Transforms IP addresses to a unique identifier in the logs"
  filename         = data.archive_file.scrub_ip_addresses.output_path
  source_code_hash = data.archive_file.scrub_ip_addresses.output_base64sha256
  function_name    = "massgov-pfml-${var.environment_name}-scrub-ip-addresses"
  handler          = "scrub_ip_addresses.handler" # the entrypoint of the newrelic instrumentation layer
  role             = aws_iam_role.scrub_ip_lambda_role.arn
  layers           = [local.newrelic_log_ingestion_layer]
  runtime          = var.runtime_py
  publish          = "false"

  environment {
    variables = {
      ENVIRONMENT                           = var.environment_name
      NEW_RELIC_ACCOUNT_ID                  = "2837112"        # PFML account
      NEW_RELIC_TRUSTED_ACCOUNT_KEY         = "1606654"        # EOLWD parent account
      NEW_RELIC_LAMBDA_HANDLER              = "lambda.handler" # the actual lambda entrypoint
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[local.constants_env]
  })
}
# Transforms the `scrub_ip_addresses.py` file in to something the lambda can use
data "archive_file" "scrub_ip_addresses" {
  type        = "zip"
  output_path = "${path.module}/.zip/scrub-ip-addresses.zip"

  source {
    filename = "scrub_ip_addresses.py"
    content  = file("${path.module}/scrub_ip_addresses.py")
  }
}
