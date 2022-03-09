#
# Terraform configuration for Payments 1099 processing task.
#
# This task is a special case because it contains two containers within one ECS task definition.
#

data "aws_ecr_repository" "pdf_api" {
  name = "pfml-pdf-api"
}

resource "aws_ecs_task_definition" "ecs_tasks_1099" {
  family                   = "${local.app_name}-${var.environment_name}-pub-payments-process-1099-documents"
  task_role_arn            = aws_iam_role.pub_payments_process_1099_task_role.arn
  execution_role_arn       = aws_iam_role.task_executor.arn
  cpu                      = 4096
  memory                   = 8192
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })

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

      environment = [for val in concat(local.common, local.db_access, local.fineos_api_access, local.fineos_s3_access, local.pub_s3_folders, local.irs_1099_documents) : val if contains(keys(val), "value")]
      secrets     = [for val in concat(local.common, local.db_access, local.fineos_api_access, local.fineos_s3_access, local.pub_s3_folders, local.irs_1099_documents) : val if !contains(keys(val), "value")]
    },
    {
      name                   = "pub-payments-process-1099-dot-net-generator-service",
      image                  = format("%s:%s", data.aws_ecr_repository.pdf_api.repository_url, var.service_docker_tag),
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
      portMappings = [
        {
          containerPort = 5000,
          hostPort      = 5000
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_tasks.name,
          "awslogs-region"        = data.aws_region.current.name,
          "awslogs-stream-prefix" = var.environment_name
        }
      },

      environment = [for val in concat(local.common, local.apps_netcore_env) : val if contains(keys(val), "value")]
      secrets     = [for val in local.common : val if !contains(keys(val), "value")]
    }
  ])
}
