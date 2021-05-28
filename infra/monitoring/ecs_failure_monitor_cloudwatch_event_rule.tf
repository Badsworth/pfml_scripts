# Make cloudwatch event
resource "aws_cloudwatch_event_rule" "ecs_failure_monitor" {
  name          = "ecs-failure-monitor"
  description   = "Monitors ECS tasks and triggers on any that fail to start"
  event_pattern = <<EOF
{
  "source": [
    "aws.ecs"
  ],
  "detail-type": [
    "ECS Task State Change"
  ],
  "detail": {
    "stopCode": ["TaskFailedToStart"],
    "lastStatus": ["STOPPED"]
  }
}
EOF
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "ecs_monitor_lambda_target" {
  arn  = aws_lambda_function.ecs_failure_monitor.arn
  rule = aws_cloudwatch_event_rule.ecs_failure_monitor.id
}

resource "aws_lambda_permission" "ecs_monitor_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ecs_failure_monitor.function_name
  principal     = "events.amazonaws.com"
}
