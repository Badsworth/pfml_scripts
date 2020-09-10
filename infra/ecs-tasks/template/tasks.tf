# Templating and configurations for ECS tasks.
#
# If you need to add a new ECS task, add it to the locals.tasks variable
# in the following format:
#
# "${local.app_name}-your-task-name" = {
#   command = ["the-command-name"],
#   task_role = null
# }
#
# This command name usually comes from pyproject.toml.
#
# The task_role should be defined, but can be null if your running task does not need
# to be assigned an IAM role for additional permissions to AWS resources.
# If not null, it should have a task_role_arn stored in it for the aws_ecs_task_definition
#
# Once this is done, apply your terraform changes and test your new ECS task
# in the test environment.
#
# From the root of the git repository (example):
#
# ./bin/run-ecs-task/run-task.sh test db-migrate-up kevin.yeh
#
locals {
  tasks = {
    "${local.app_name}-db-migrate-up" = {
      command   = ["db-migrate-up"],
      task_role = null
    },
    "${local.app_name}-db-admin-create-db-users" = {
      command   = ["db-admin-create-db-users"],
      task_role = null
    },
    "${local.app_name}-${var.environment_name}-ad-hoc-verification" = {
      command = ["generate-verification-codes",
        "--input=s3://massgov-pfml-${var.environment_name}-verification-codes/source.csv",
      "--output=s3://massgov-pfml-${var.environment_name}-verification-codes/output.csv"],
      task_role = aws_iam_role.task_adhoc_verification_task_role.arn
    }
  }
}

data "aws_ecr_repository" "app" {
  name = local.app_name
}

resource "aws_ecs_task_definition" "ecs_tasks" {
  for_each                 = local.tasks
  family                   = each.key
  execution_role_arn       = aws_iam_role.task_executor.arn
  container_definitions    = data.template_file.task_container_definitions[each.key].rendered
  task_role_arn            = each.value.task_role
  cpu                      = "512"
  memory                   = "1024"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
}

data "template_file" "task_container_definitions" {
  for_each = local.tasks
  template = file("${path.module}/json/task_template.json")

  vars = {
    app_name                   = local.app_name
    task_name                  = each.key
    command                    = jsonencode(each.value.command)
    cpu                        = "512"
    memory                     = "1024"
    db_host                    = data.aws_db_instance.default.address
    db_name                    = data.aws_db_instance.default.db_name
    db_username                = data.aws_db_instance.default.master_username
    docker_image               = "${data.aws_ecr_repository.app.repository_url}:${var.service_docker_tag}"
    environment_name           = var.environment_name
    cloudwatch_logs_group_name = aws_cloudwatch_log_group.ecs_tasks.name
    aws_region                 = data.aws_region.current.name
  }
}
