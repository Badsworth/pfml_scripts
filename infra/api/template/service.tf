# Terraform configuration for running applications on ECS Fargate. Applications are run
# in a private subnet behind a network load balancer.
#
data "aws_ecr_repository" "app" {
  name = local.app_name
}

resource "aws_ecs_service" "app" {
  name            = "${local.app_name}-${var.environment_name}"
  task_definition = aws_ecs_task_definition.app.arn
  cluster         = var.service_ecs_cluster_arn
  launch_type     = "FARGATE"
  desired_count   = var.service_app_count

  network_configuration {
    assign_public_ip = false
    subnets          = data.aws_subnet.app.*.id
    security_groups  = [aws_security_group.app.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.id
    container_name   = local.app_name
    container_port   = 1550
  }

  depends_on = [
    aws_lb_listener.listener,
    aws_iam_role_policy.task_executor,
  ]
}

resource "aws_ecs_task_definition" "app" {
  family                = local.app_name
  execution_role_arn    = aws_iam_role.task_executor.arn
  container_definitions = data.template_file.container_definitions.rendered

  cpu                      = "1024"
  memory                   = "2048"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
}

data "template_file" "container_definitions" {
  template = file("${path.module}/container_definitions.json")

  vars = {
    app_name                   = local.app_name
    cpu                        = "512"
    memory                     = "1024"
    docker_image               = "${data.aws_ecr_repository.app.repository_url}:${var.service_docker_tag}"
    environment_name           = var.environment_name
    cloudwatch_logs_group_name = aws_cloudwatch_log_group.service_logs.name
    aws_region                 = data.aws_region.current.name
  }
}
