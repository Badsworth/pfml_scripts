#WIP not for merge

# locals {
#   tasks = {

#   }

data "aws_ecr_repository" "app" {
  name = local.app_name
}

resource "aws_ecs_task_definition" "ecs_tasks_bi" {
  family                   = "${local.app_name}-${var.environment_name}-BI-python"
  task_role_arn            = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-BI-python"
  execution_role_arn       = aws_iam_role.task_executor.arn
  cpu                      = tostring(4096)
  memory                   = tostring(8192)
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })

  container_definitions = jsonencode([
    {
      name                   = "BI-python",
      image                  = format("%s:%s", data.aws_ecr_repository.app.repository_url, var.service_docker_tag),
      command                = "bi-python" #add from toml,
      cpu                    = lookup(each.value, "cpu", 1024),
      memory                 = lookup(each.value, "memory", 2048),
      networkMode            = "awsvpc",
      essential              = true,
      readonlyRootFilesystem = false, # False by default; some tasks write local files.
      linuxParameters = {
        capabilities = {
          drop = ["ALL"]
        },
        initProcessEnabled = true
      },
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_tasks.name,
          "awslogs-region"        = data.aws_region.current.name,
          "awslogs-stream-prefix" = var.environment_name
        }
      },

      environment = []
      secrets     = []
    }
  ])
}
