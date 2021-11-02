# Templating and configurations for ECS tasks with multiple containers
# NOTE: Pushed for collaboration. NOT READY TO MERGE

# this resource is used as a template to provision each ECS task in local.tasks
resource "aws_ecs_task_definition" "ecs_tasks_1099" {
  family                   = "${local.app_name}-${var.environment_name}-1099-form-generator"
  task_role_arn            = null
  execution_role_arn       = aws_iam_role.task_executor.arn
  cpu                      = tostring(4096)
  memory                   = tostring(8192)
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })

  //
  // This json needs to be dynamically created with each iteration
  // See task.tf
  //
  container_definitions = jsonencode([
    {
      name                   = "pub-payments-process-1099-documents",
      image                  = "498823821309.dkr.ecr.us-east-1.amazonaws.com/pfml-api-dot-net-1099:latest",
      command                = ["pub-payments-process-1099-documents"],
      cpu                    = 2048,
      memory                 = 4096,
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
    },
    {
      name                   = "pub-payments-process-1099-dot-net-generator-service",
      image                  = "498823821309.dkr.ecr.us-east-1.amazonaws.com/pfml-api-dot-net-1099:latest",
      command                = ["dotnet", "PfmlPdfApi.dll"],
      cpu                    = 2048,
      memory                 = 4096,
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
