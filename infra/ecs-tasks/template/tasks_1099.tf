# Templating and configurations for ECS tasks with multiple containers
# NOTE: Pushed for collaboration. NOT READY TO MERGE

# this resource is used as a template to provision each ECS task in local.tasks
resource "aws_ecs_task_definition" "ecs_tasks_1099" {
  family                   = "${local.app_name}-${var.environment_name}-1099-form-generator"
  task_role_arn            = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099"
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
      image                  = format("%s:%s", data.aws_ecr_repository.app.repository_url, var.service_docker_tag),
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

      environment = [for val in concat(local.common, local.db_access, local.fineos_s3_access, local.pub_s3_folders) : val if contains(keys(val), "value")]
      secrets     = [for val in concat(local.common, local.db_access, local.fineos_s3_access, local.pub_s3_folders) : val if !contains(keys(val), "value")]
    },
    {
      name                   = "pub-payments-process-1099-dot-net-generator-service",
      image                  = "498823821309.dkr.ecr.us-east-1.amazonaws.com/pfml-api-1099:latest",
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

      environment = [for val in local.common : val if contains(keys(val), "value")]
      secrets     = [for val in local.common : val if !contains(keys(val), "value")]
    }
  ])
}
