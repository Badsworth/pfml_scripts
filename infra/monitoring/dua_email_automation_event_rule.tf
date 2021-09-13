# Make cloudwatch event
resource "aws_cloudwatch_event_rule" "dua_email_automation" {
  name        = "dua-email-automation"
  description = "Automates sending of DUA DFML file"
  # Event rule triggers every day at 1300 GMT (8am EST UTC−05:00)
  schedule_expression = "cron(0 13 * * ? *)"
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "dua_email_automation_lambda_target" {
  arn  = aws_lambda_function.dua_email_automation.arn
  rule = aws_cloudwatch_event_rule.dua_email_automation.id
}

resource "aws_lambda_permission" "dua_email_automation_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dua_email_automation.function_name
  principal     = "events.amazonaws.com"
}
