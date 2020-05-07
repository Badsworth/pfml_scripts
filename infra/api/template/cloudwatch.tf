# Cloudwatch log group to for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "service_logs" {
  name = "service/${local.app_name}-${var.environment_name}"
}

# Cloudwatch log group to for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "db_migrate_logs" {
  name = "service/${local.app_name}-${var.environment_name}/db-migrate"
}
