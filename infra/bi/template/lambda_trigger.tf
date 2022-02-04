locals {
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = module.constants.newrelic_log_ingestion_arn
}
# ------------------------------------------------------------------------------------------
data "aws_iam_policy_document" "bi_reporting_lambda_assumed_role" {
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

resource "aws_iam_role" "bi_reporting_lambda_role" {
  name               = "mass-pfml-${var.environment_name}-bi-reporting-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.bi_reporting_lambda_assumed_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_executor" {
  role = aws_iam_role.bi_reporting_lambda_role.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "bi_reporting_lambda" {
  description      = "Validates data from FINEOS files for Qlik"
  filename         = data.archive_file.bi_reporting_lambda.output_path
  source_code_hash = data.archive_file.bi_reporting_lambda.output_base64sha256
  function_name    = "massgov-pfml-${var.environment_name}-bi-reporting-lambda"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.bi_reporting_lambda_role.arn
  runtime          = var.runtime_py
  memory_size      = "4096"
  publish          = "false"
  timeout          = "240"

  environment {
    variables = {
      ENVIRONMENT = var.environment_name
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_lambda_permission" "run_bi_reporting_lambda" {
  statement_id   = "TriggerExecutionFromS3"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.bi_reporting_lambda.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = data.aws_s3_bucket.business_intelligence_tool.arn
  source_account = data.aws_caller_identity.current.account_id
}

resource "aws_cloudwatch_log_subscription_filter" "nr_bi_reporting_lambda" {
  name            = "nr_bi_reporting_lambda"
  log_group_name  = "/aws/lambda/massgov-pfml-${var.environment_name}-bi-reporting-lambda"
  filter_pattern  = ""
  destination_arn = module.constants.newrelic_log_ingestion_arn
  depends_on      = [aws_lambda_function.bi_reporting_lambda]
}

resource "aws_s3_bucket_notification" "bi_reporting_lambda_trigger" {
  bucket = data.aws_s3_bucket.business_intelligence_tool.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.bi_reporting_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "fineos/dataexports/"
    filter_suffix       = ".csv"
  }


  depends_on = [
    aws_lambda_permission.run_bi_reporting_lambda,
    aws_lambda_function.bi_reporting_lambda,
    aws_iam_role.bi_reporting_lambda_role
  ]
}


data "archive_file" "bi_reporting_lambda" {
  type        = "zip"
  output_path = "${path.module}/.zip/lambda_function.zip"

  source {
    filename = "lambda_function.py"
    content  = file("${path.module}/lambda_function.py")
  }
}