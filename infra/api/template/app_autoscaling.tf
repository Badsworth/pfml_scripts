
resource "aws_appautoscaling_policy" "ecs_scale_policy" {
  name               = "${var.environment_name}-${local.app_name}-ecs-scale-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"

    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
    target_value       = 60
  }
  depends_on = [
    aws_appautoscaling_target.ecs_target
  ]

}

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.service_max_app_count
  min_capacity       = var.service_app_count
  resource_id        = "service/${var.environment_name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}