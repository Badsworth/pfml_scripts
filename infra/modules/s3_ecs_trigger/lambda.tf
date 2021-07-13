# Lambda that runs an ECS task.
#
locals {
  newrelic_log_ingestion_layer = "arn:aws:lambda:us-east-1:451483290750:layer:NewRelicPython38:16"
}

resource "aws_lambda_function" "task_trigger" {
  description      = "Launch ECS task"
  filename         = data.archive_file.task_trigger_lambda.output_path
  source_code_hash = data.archive_file.task_trigger_lambda.output_base64sha256
  function_name    = "${var.task_name}-${var.environment_name}-task-trigger"
  handler          = "newrelic_lambda_wrapper.handler" # the entrypoint of the newrelic instrumentation layer
  role             = aws_iam_role.task_trigger.arn
  layers           = [local.newrelic_log_ingestion_layer]
  runtime          = "python3.8"
  publish          = "false"
  timeout          = 60 # 1 minute

  vpc_config {
    subnet_ids         = var.app_subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      ENVIRONMENT                           = var.environment_name
      NEW_RELIC_ACCOUNT_ID                  = "2837112"         # PFML account
      NEW_RELIC_TRUSTED_ACCOUNT_KEY         = "1606654"         # EOLWD parent account
      NEW_RELIC_LAMBDA_HANDLER              = "handler.handler" # the actual lambda entrypoint
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
      ECS_TASK_DEFINITION                   = var.ecs_task_definition_family
      SUBNETS                               = join(",", var.app_subnet_ids)
      SECURITY_GROUPS                       = join(",", var.security_group_ids)
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

data "archive_file" "task_trigger_lambda" {
  type        = "zip"
  output_path = "${abspath(path.module)}/.zip/${var.task_name}_handler.zip"

  source {
    filename = "handler.py"
    content  = file("${abspath(path.module)}/handler.py")
  }
}

resource "aws_cloudwatch_log_group" "task_trigger_lambda" {
  name = "/aws/lambda/${aws_lambda_function.task_trigger.function_name}"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# Allow the Lambda to be invoked by S3
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.task_trigger.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_bucket_arn
}

resource "aws_cloudwatch_log_subscription_filter" "nr_lambda_task_trigger" {
  name            = "nr_lambda_task_trigger"
  log_group_name  = aws_cloudwatch_log_group.task_trigger_lambda.name
  filter_pattern  = ""
  destination_arn = module.constants.newrelic_log_ingestion_arn
}
