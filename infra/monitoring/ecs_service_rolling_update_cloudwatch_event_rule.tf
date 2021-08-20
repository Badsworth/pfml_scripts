# Make cloudwatch event
resource "aws_cloudwatch_event_rule" "ecs_service_rolling_update" {
  name        = "ecs-service-rolling-update"
  description = "Performs daily rolling-update on PFML-API service in each cluster"
  # Event rule triggers every day at 1300 GMT (8am EST UTC−05:00)
  schedule_expression = "cron(0 13 * * ? *)"
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "ecs_service_rolling_update_lambda_target" {
  arn  = aws_lambda_function.ecs_service_rolling_update.arn
  rule = aws_cloudwatch_event_rule.ecs_service_rolling_update.id
}

resource "aws_lambda_permission" "ecs_service_rolling_update_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ecs_service_rolling_update.function_name
  principal     = "events.amazonaws.com"
}
