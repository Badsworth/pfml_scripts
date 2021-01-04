# Autoscaling policies and related resources for API lambdas.

resource "aws_appautoscaling_target" "cognito_post_conf" {
  count = var.cognito_enable_provisioned_concurrency ? 1 : 0
  depends_on = [
    aws_lambda_function.cognito_post_confirmation,
    aws_lambda_alias.cognito_post_confirmation__latest,
    aws_lambda_provisioned_concurrency_config.cognito_post_confirmation_concurrency_settings[0]
  ]

  min_capacity       = 0
  max_capacity       = aws_lambda_provisioned_concurrency_config.cognito_post_confirmation_concurrency_settings[0].provisioned_concurrent_executions
  resource_id        = "function:${aws_lambda_function.cognito_post_confirmation.function_name}:${aws_lambda_alias.cognito_post_confirmation__latest[0].name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_scheduled_action" "scale_out__cognito_post_conf" {
  count      = var.cognito_enable_provisioned_concurrency ? 1 : 0
  depends_on = [aws_appautoscaling_target.cognito_post_conf]

  name               = "weekday_am_scale_out"
  schedule           = "cron(45 13 ? * MON-FRI *)" # monday thru friday, 8:45am EST
  resource_id        = "function:${aws_lambda_function.cognito_post_confirmation.function_name}:${aws_lambda_alias.cognito_post_confirmation__latest[0].name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"

  scalable_target_action {
    # Enable the normal amount of provisioned concurrency (five instances) during working hours on weekdays.
    min_capacity = var.cognito_provisioned_concurrency_level_max
    max_capacity = var.cognito_provisioned_concurrency_level_max
  }
}

resource "aws_appautoscaling_scheduled_action" "scale_in__cognito_post_conf" {
  count      = var.cognito_enable_provisioned_concurrency ? 1 : 0
  depends_on = [aws_appautoscaling_target.cognito_post_conf]

  name               = "weeknight_pm_scale_in"
  schedule           = "cron(15 22 ? * MON-FRI *)" # monday thru friday, 5:15pm EST
  resource_id        = "function:${aws_lambda_function.cognito_post_confirmation.function_name}:${aws_lambda_alias.cognito_post_confirmation__latest[0].name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"

  scalable_target_action {
    # Keep one instance hot outside of business hours. This will allow quick response times for anyone who signs up on nights or weekends.
    min_capacity = var.cognito_provisioned_concurrency_level_min
    max_capacity = var.cognito_provisioned_concurrency_level_min
  }
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_appautoscaling_target" "cognito_pre_signup" {
  count = var.cognito_enable_provisioned_concurrency ? 1 : 0
  depends_on = [
    aws_lambda_function.cognito_pre_signup,
    aws_lambda_alias.cognito_pre_signup__latest,
    aws_lambda_provisioned_concurrency_config.cognito_pre_signup_concurrency_settings[0]
  ]

  min_capacity       = 0
  max_capacity       = aws_lambda_provisioned_concurrency_config.cognito_pre_signup_concurrency_settings[0].provisioned_concurrent_executions
  resource_id        = "function:${aws_lambda_function.cognito_pre_signup.function_name}:${aws_lambda_alias.cognito_pre_signup__latest[0].name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_scheduled_action" "scale_out__cognito_pre_signup" {
  count      = var.cognito_enable_provisioned_concurrency ? 1 : 0
  depends_on = [aws_appautoscaling_target.cognito_pre_signup]

  name               = "weekday_am_scale_out"
  schedule           = "cron(45 13 ? * MON-FRI *)" # monday thru friday, 8:45am EST
  resource_id        = "function:${aws_lambda_function.cognito_pre_signup.function_name}:${aws_lambda_alias.cognito_pre_signup__latest[0].name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"

  scalable_target_action {
    # Enable the normal amount of provisioned concurrency (five instances) during working hours on weekdays.
    min_capacity = var.cognito_provisioned_concurrency_level_max
    max_capacity = var.cognito_provisioned_concurrency_level_max
  }
}

resource "aws_appautoscaling_scheduled_action" "scale_in__cognito_pre_signup" {
  count      = var.cognito_enable_provisioned_concurrency ? 1 : 0
  depends_on = [aws_appautoscaling_target.cognito_pre_signup]

  name               = "weeknight_pm_scale_in"
  schedule           = "cron(15 22 ? * MON-FRI *)" # monday thru friday, 5:15pm EST
  resource_id        = "function:${aws_lambda_function.cognito_pre_signup.function_name}:${aws_lambda_alias.cognito_pre_signup__latest[0].name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"

  scalable_target_action {
    # Keep one instance hot outside of business hours. This will allow quick response times for anyone who signs up on nights or weekends.
    min_capacity = var.cognito_provisioned_concurrency_level_min
    max_capacity = var.cognito_provisioned_concurrency_level_min
  }
}
