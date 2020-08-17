# Cloudwatch log group for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "service_logs" {
  name = "service/${local.app_name}-${var.environment_name}"
}

resource "aws_cloudwatch_event_target" "trigger_dor_import_lambda_daily_at_11_pm" {
  rule      = aws_cloudwatch_event_rule.daily_11pm_et.name
  arn       = aws_lambda_function.dor_import.arn
  target_id = "dor_import_${var.environment_name}_lambda_event_target"
}

resource "aws_cloudwatch_event_rule" "daily_11pm_et" {
  name        = "daily-at-11-pm"
  description = "Fires once daily at 11pm US EDT/3am UTC"
  # The time of day can only be specified in UTC and will need to be updated when daylight savings changes occur, if the 2300 US ET is desired to be consistent.
  schedule_expression = "cron(0 03 * * ? *)"
}


resource "aws_lambda_permission" "allow_cloudwatch_to_call_dor_import" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dor_import.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_11pm_et.arn
}
