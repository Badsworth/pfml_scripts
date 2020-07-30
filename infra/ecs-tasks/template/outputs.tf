output "security_groups" {
  value = [aws_security_group.tasks.id]
}

output "migrate_up_task_arn" {
  value = aws_ecs_task_definition.db_migrate_up.arn
}

output "create_db_users_task_arn" {
  value = aws_ecs_task_definition.create_db_users.arn
}
