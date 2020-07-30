output "cognito_post_confirmation_lambda_arn" {
  value = aws_lambda_function.cognito_post_confirmation.arn
}

output "ecs_service_id" {
  value = aws_ecs_service.app.id
}
