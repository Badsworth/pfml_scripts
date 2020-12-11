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
    target_value       = 60 # Leaving this at 60% to test in LST
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

# Stop API service each weekday at midnight ET.
# This should match the RDS downtime schedule in rds.tf.
#
# * NOTE: Currently off to support overtime activities.
resource "aws_appautoscaling_scheduled_action" "ecs_api_stop" {
  count              = 0
  name               = "${local.app_name}-${var.environment_name}-shutdown"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  scalable_target_action {
    min_capacity = 0
    max_capacity = 0
  }

  # Stop API service at the end of every weekday at midnight (5AM UTC on the next day)
  # This is an hour off during daylight savings time but it works well enough.
  schedule = "cron(00 5 ? * TUE-SAT *)"
}

# Start API service each weekday at 7am ET.
# This should match the RDS downtime schedule in rds.tf.
#
# * NOTE: Currently off to support overtime activities.
resource "aws_appautoscaling_scheduled_action" "ecs_api_start" {
  count              = 0
  name               = "${local.app_name}-${var.environment_name}-start"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  scalable_target_action {
    min_capacity = var.service_app_count
    max_capacity = var.service_max_app_count
  }

  # Start API service every weekday at 7AM Eastern, 12PM UTC
  # This is an hour off during daylight savings time but it works well enough.
  schedule = "cron(00 12 ? * MON-FRI *)"
}
