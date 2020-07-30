# Cloudwatch log group to for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "db_migrate_logs" {
  name = "service/${local.app_name}-${var.environment_name}/db-migrate"
}

# Cloudwatch log group for rds
resource "aws_cloudwatch_log_group" "create_db_users_logs" {
  name = "service/${local.app_name}-${var.environment_name}/create-db-users"
}
