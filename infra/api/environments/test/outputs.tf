output "cognito_post_confirmation_lambda_arn" {
  value = module.api.cognito_post_confirmation_lambda_arn
}

output "ecs_cluster_arn" {
  value = data.aws_ecs_cluster.test.arn
}

output "ecs_service_id" {
  value = module.api.ecs_service_id
}
