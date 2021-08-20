# Lambda assume role policy 
data "aws_iam_policy_document" "ecs_service_rolling_update_lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Lambda ecs permissions policy
data "aws_iam_policy_document" "ecs_service_rolling_update_inline_policy" {
  statement {
    actions   = ["ecs:ListClusters", "ecs:UpdateService"]
    resources = ["*"]
  }
}

# IAM Role for lambda
resource "aws_iam_role" "ecs_service_rolling_update_lambda_role" {
  name               = "mass-pfml-ecs-service-rolling-update-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_service_rolling_update_lambda_assume_role.json

  inline_policy {
    name   = "ecs-service-rolling-update"
    policy = data.aws_iam_policy_document.ecs_service_rolling_update_inline_policy.json
  }
}

# Allow lambda to create logs
resource "aws_iam_role_policy_attachment" "ecs_service_rolling_update_lambda_basic_executor" {
  role = aws_iam_role.ecs_service_rolling_update_lambda_role.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "ecs_service_rolling_update" {
  description      = "Updates (restarts) pfml API ECS services"
  filename         = data.archive_file.ecs_service_rolling_update_lambda_code.output_path
  source_code_hash = data.archive_file.ecs_service_rolling_update_lambda_code.output_base64sha256
  function_name    = "massgov-pfml-ecs-service-rolling-update"
  handler          = "ecs_service_rolling_update_lambda.lambda_handler"
  role             = aws_iam_role.ecs_service_rolling_update_lambda_role.arn
  runtime          = "python3.8"
  publish          = "false"
  timeout          = 60 # 1 minute

  tags = module.constants.common_tags
}

data "archive_file" "ecs_service_rolling_update_lambda_code" {
  type        = "zip"
  output_path = "${path.module}/.zip/ecs_service_rolling_update_lambda.zip"

  source {
    filename = "ecs_service_rolling_update_lambda.py"
    content  = file("${path.module}/ecs_service_rolling_update_lambda.py")
  }
}
