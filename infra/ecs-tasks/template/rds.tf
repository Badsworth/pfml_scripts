data "aws_db_instance" "default" {
  db_instance_identifier = "massgov-pfml-${var.environment_name}"
}

data "aws_security_group" "rds_postgresql" {
  name = "${local.app_name}-rds-${var.environment_name}"
}
