resource "aws_ecs_task_definition" "db_migrate_up" {
  family                = "${local.app_name}-migrate-up"
  execution_role_arn    = aws_iam_role.task_executor.arn
  container_definitions = data.template_file.db_migrate_up_container_definitions.rendered

  cpu                      = "512"
  memory                   = "1024"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
}

data "template_file" "db_migrate_up_container_definitions" {
  template = file("${path.module}/tasks/db_migrate_up.json")

  vars = {
    app_name                   = local.app_name
    cpu                        = "512"
    memory                     = "1024"
    db_url                     = aws_db_instance.default.address
    db_name                    = aws_db_instance.default.name
    db_username                = aws_db_instance.default.username
    docker_image               = "${data.aws_ecr_repository.app.repository_url}:${var.service_docker_tag}"
    environment_name           = var.environment_name
    cloudwatch_logs_group_name = aws_cloudwatch_log_group.db_migrate_logs.name
    aws_region                 = data.aws_region.current.name
  }
}
