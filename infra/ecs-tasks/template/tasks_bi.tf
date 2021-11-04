#WIP not for merge

# locals {
#   tasks = {

#   }

data "aws_ecr_repository" "app" {
  name = local.app_name
}

# this resource is used as a template to provision each ECS task in local.tasks
resource "aws_ecs_task_definition" "ecs_tasks" {
  for_each                 = local.tasks
  family                   = "${local.app_name}-${var.environment_name}-${each.key}"
  task_role_arn            = lookup(each.value, "task_role", null)
  execution_role_arn       = lookup(each.value, "execution_role", aws_iam_role.task_executor.arn)
  cpu                      = tostring(lookup(each.value, "cpu", 1024))
  memory                   = tostring(lookup(each.value, "memory", 2048))
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })

  container_definitions = jsonencode([
    {
      name                   = each.key,
      image                  = format("%s:%s", data.aws_ecr_repository.app.repository_url, var.service_docker_tag),
      command                = each.value.command,
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

      # Split env into static environment variables or secrets based on whether they contain "value" or "valueFrom"
      # I know, it's not very readable but this is how terraform is.
      #
      # We use !contains("value") for secrets instead of contains("valueFrom") so that any items with typos are
      # caught and error out when trying to apply the task definition. Otherwise, anything with a typo could
      # silently cause env vars to go missing which would definitely confuse someone for a day or two.
      #
      environment = [for val in flatten(concat(lookup(each.value, "env", []), local.common)) : val if contains(keys(val), "value")]
      secrets     = [for val in flatten(concat(lookup(each.value, "env", []), local.common)) : val if !contains(keys(val), "value")]
    }
  ])
}
