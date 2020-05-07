output "security_groups" {
  value = [aws_security_group.app.id]
}

output "migrate_up_task_arn" {
  value = aws_ecs_task_definition.db_migrate_up.arn
}
