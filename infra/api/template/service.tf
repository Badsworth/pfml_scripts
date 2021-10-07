# Terraform configuration for running applications on ECS Fargate. Applications are run
# in a private subnet behind a network load balancer.
#
data "aws_ecr_repository" "app" {
  name = local.app_name
}

resource "aws_ecs_service" "app" {
  name             = "${local.app_name}-${var.environment_name}"
  task_definition  = aws_ecs_task_definition.app.arn
  cluster          = var.service_ecs_cluster_arn
  launch_type      = "FARGATE"
  platform_version = "1.4.0"
  desired_count    = var.service_app_count

  # WORKAROUND: Increase health check grace period to 5 minutes to account for
  # lag time in NLB starting to send requests to new tasks.
  health_check_grace_period_seconds = 300

  # Allow changes to the desired_count without differences in terraform plan.
  # This allows autoscaling to manage the desired count for us.
  lifecycle {
    ignore_changes = [desired_count]
  }

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
  family                = "${local.app_name}-${var.environment_name}-server"
  execution_role_arn    = aws_iam_role.task_executor.arn
  task_role_arn         = aws_iam_role.api_service.arn
  container_definitions = data.template_file.container_definitions.rendered

  cpu                      = "1024"
  memory                   = "2048"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

data "template_file" "container_definitions" {
  template = file("${path.module}/container_definitions.json")

  vars = {
    app_name                                   = local.app_name
    cpu                                        = "768"
    memory                                     = "1536"
    db_host                                    = aws_db_instance.default.address
    db_name                                    = aws_db_instance.default.name
    db_username                                = "pfml_api"
    docker_image                               = "${data.aws_ecr_repository.app.repository_url}:${var.service_docker_tag}"
    environment_name                           = var.environment_name
    enable_full_error_logs                     = var.enable_full_error_logs
    cloudwatch_logs_group_name                 = aws_cloudwatch_log_group.service_logs.name
    aws_region                                 = data.aws_region.current.name
    cors_origins                               = join(",", var.cors_origins)
    cognito_user_pool_id                       = var.cognito_user_pool_id
    cognito_user_pool_client_id                = var.cognito_user_pool_client_id
    cognito_user_pool_keys_url                 = var.cognito_user_pool_keys_url
    logging_level                              = var.logging_level
    rmv_client_certificate_binary_arn          = var.rmv_client_certificate_binary_arn
    rmv_client_base_url                        = var.rmv_client_base_url
    rmv_api_behavior                           = var.rmv_api_behavior
    rmv_check_mock_success                     = var.rmv_check_mock_success
    fineos_client_customer_api_url             = var.fineos_client_customer_api_url
    fineos_client_integration_services_api_url = var.fineos_client_integration_services_api_url
    fineos_client_group_client_api_url         = var.fineos_client_group_client_api_url
    fineos_client_wscomposer_api_url           = var.fineos_client_wscomposer_api_url
    fineos_client_wscomposer_user_id           = var.fineos_client_wscomposer_user_id
    fineos_client_oauth2_url                   = var.fineos_client_oauth2_url
    fineos_client_oauth2_client_id             = var.fineos_client_oauth2_client_id
    service_now_base_url                       = var.service_now_base_url
    portal_base_url                            = var.portal_base_url
    admin_portal_base_url                      = var.admin_portal_base_url
    enable_application_fraud_check             = var.enable_application_fraud_check
    release_version                            = var.release_version
    new_plan_proofs_active_at                  = var.new_plan_proofs_active_at
  }
}
