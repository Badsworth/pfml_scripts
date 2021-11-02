# Templating and configurations for ECS tasks with multiple containers
# NOTE: Pushed for collaboration. NOT READY TO MERGE
data "aws_ecr_repository" "app" {
  name = local.app_name
}

locals {
  tasks = {
    "pub-payments-process-1099" = [
      "pub-payments-process-1099-batch" = {
        command   = ["pub-payments-process-1099-batch"]
        task_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099"
        env = [
            local.db_access,
            local.fineos_s3_access,
            local.pub_s3_folders
        ]
      },
      "pub-payments-process-1099-api" = {
        command   = ["pub-payments-process-1099-api"]
        task_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099"
        env = [
            local.pub_s3_folders
        ]
      },
    ]
  }
}

# this resource is used as a template to provision each ECS task in local.tasks
resource "aws_ecs_task_definition" "ecs_tasks_multi" {
  for_each = local.tasks

  //
  // This json needs to be dynamically created with each iteration
  // See task.tf
  //
  container_definitions = jsonencode([
    {

    },
    {

    }
  ])
}
