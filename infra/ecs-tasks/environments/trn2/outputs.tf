output "subnets" {
  value = data.aws_subnet_ids.vpc_app.ids
}

output "security_groups" {
  value = module.tasks.security_groups
}

output "ecs_task_arns" {
  value = module.tasks.ecs_task_arns
}
