output "security_groups" {
  value = [aws_security_group.tasks.id]
}

output "ecs_task_arns" {
  value = {
    for taskname in keys(aws_ecs_task_definition.ecs_tasks) :
    taskname => aws_ecs_task_definition.ecs_tasks[taskname].arn
  }
}
