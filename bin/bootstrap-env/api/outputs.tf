output "subnets" {
  value = data.aws_subnet_ids.vpc_app.ids
}

output "security_groups" {
  value = module.api.security_groups
}

output "migrate_up_task_arn" {
  value = module.api.migrate_up_task_arn
}

output "cognito_post_confirmation_lambda_arn" {
  value = module.api.cognito_post_confirmation_lambda_arn
}
