locals {
  app_name = "pfml-api"
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = module.constants.newrelic_log_ingestion_arn
}

# ECS cluster for running applications in an environment.
#
# Applications within this cluster are not actually tied
# to a VPC/environment, but we separate them to improve
# organization and simplify lookups.
resource "aws_ecs_cluster" "cluster" {
  name = var.environment_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[local.constants_env]
    "SMX:Asset" = "v1:${var.environment_name}:${module.constants.smartronix_environment_tags[var.environment_name]}:ECS:PFML:Advanced:None"
  })
}

###### ECS Task Stopped State Events Monitoring

resource "aws_cloudwatch_log_group" "ecs_tasks_events" {
  name = "service/${local.app_name}-${var.environment_name}/ecs-tasks/events"
}

resource "aws_cloudwatch_event_rule" "ecs_tasks_events" {
  name          = "ecs-tasks-events"
  description   = "Monitors ECS tasks all events"
  event_pattern = <<EOF
  {
    "source": [
      "aws.ecs"
    ],
    "detail-type": [
      "ECS Task State Change"
    ],
    "detail": {
      "desiredStatus": ["STOPPED"],
      "clusterArn": ["${aws_ecs_cluster.cluster.arn}"]
    }
  }
  EOF
}

resource "aws_cloudwatch_event_target" "ecs_tasks_events_target" {
  arn  = aws_cloudwatch_log_group.ecs_tasks_events.arn
  rule = aws_cloudwatch_event_rule.ecs_tasks_events.id
}

resource "aws_cloudwatch_log_subscription_filter" "ecs_tasks_events_logging" {
  name            = "ecs_tasks_events_logs"
  log_group_name  = aws_cloudwatch_log_group.ecs_tasks_events.name
  destination_arn = local.newrelic_log_ingestion_lambda
  # matches all log events
  filter_pattern = ""
}

resource "aws_lambda_permission" "ecs_permission_tasks_events_logging" {
  statement_id  = "NRLambdaPermission_ECSTasksEventsLogging_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.ecs_tasks_events.arn}:*"
}

