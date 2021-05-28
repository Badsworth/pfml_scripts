locals {
  # layerfied python requests library
  requests_layer = "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-requests:16"
}

# Lambda assume role policy 
data "aws_iam_policy_document" "ecs_monitor_lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Get slack api key
data "aws_ssm_parameter" "slackbot_api_key" {
  name = "/admin/common/nava-slackbot-api-key"
}

# IAM Role for lambda
resource "aws_iam_role" "ecs_monitor_lambda_role" {
  name               = "mass-pfml-ecs-failure-monitor-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_monitor_lambda_assume_role.json
}

# Allow lambda to create logs

resource "aws_iam_role_policy_attachment" "ecs_monitor_lambda_basic_executor" {
  role = aws_iam_role.ecs_monitor_lambda_role.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "ecs_failure_monitor" {
  description      = "Triggered by CloudWatch Event Rule searching for ECS tasks that failed to start"
  filename         = data.archive_file.ecs_monitor_lambda_code.output_path
  source_code_hash = data.archive_file.ecs_monitor_lambda_code.output_base64sha256
  function_name    = "massgov-pfml-ecs-failure-monitor"
  handler          = "ecs_monitor_lambda.lambda_handler"
  role             = aws_iam_role.ecs_monitor_lambda_role.arn
  layers           = [local.requests_layer]
  runtime          = "python3.8"
  publish          = "false"

  environment {
    variables = {
      SLACK_CHANNEL_ID = module.constants.slackbot_channels["mass-pfml-pd-warnings"]
      SLACK_API_KEY    = data.aws_ssm_parameter.slackbot_api_key.value
    }
  }

  tags = module.constants.common_tags
}

data "archive_file" "ecs_monitor_lambda_code" {
  type        = "zip"
  output_path = "${path.module}/.zip/ecs_failure_monitor_lambda.zip"

  source {
    filename = "ecs_monitor_lambda.py"
    content  = file("${path.module}/ecs_failure_monitor_lambda.py")
  }
}
