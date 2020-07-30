output "subnets" {
  value = data.aws_subnet_ids.vpc_app.ids
}

output "security_groups" {
  value = module.tasks.security_groups
}

output "migrate_up_task_arn" {
  value = module.tasks.migrate_up_task_arn
}

output "create_db_users_task_arn" {
  value = module.tasks.create_db_users_task_arn
}
