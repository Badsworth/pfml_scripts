output "security_groups" {
  value = [aws_security_group.app.id]
}

output "migrate_up_task_arn" {
  value = aws_ecs_task_definition.db_migrate_up.arn
}

output "cognito_post_confirmation_lambda_arn" {
  value = aws_lambda_function.cognito_post_confirmation.arn
}
