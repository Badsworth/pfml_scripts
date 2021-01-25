output "security_groups" {
  value = [aws_security_group.tasks.id]
}

output "ecs_task_arns" {
  value = {
    for task_name in keys(aws_ecs_task_definition.ecs_tasks) :
    task_name => aws_ecs_task_definition.ecs_tasks[task_name].arn
  }
}
