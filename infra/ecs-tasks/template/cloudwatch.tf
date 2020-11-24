# Cloudwatch log group to for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "ecs_tasks" {
  name = "service/${local.app_name}-${var.environment_name}/ecs-tasks"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

locals {
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = module.constants.newrelic_log_ingestion_arn
}

resource "aws_cloudwatch_log_subscription_filter" "ecs_task_logging" {
  name            = "ecs_task_logs"
  log_group_name  = aws_cloudwatch_log_group.ecs_tasks.name
  destination_arn = local.newrelic_log_ingestion_lambda
  # matches all log events
  filter_pattern = ""
}

resource "aws_lambda_permission" "ecs_permission_tasks_logging" {
  statement_id  = "NRLambdaPermission_ECSTasksLogging_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
}
