# Setup an RDS Postgres DB for API environments

# Why is DB identifier using hyphens and name using underscore?
# https://github.com/hashicorp/terraform/issues/16784
# https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html#RDS_Limits.Constraints

data "aws_ssm_parameter" "db_password" {
  name            = "/service/${local.app_name}/${var.environment_name}/db-password"
  with_decryption = true
}

resource "aws_db_subnet_group" "rds_postgres" {
  name        = "massgov-pfml-${var.environment_name}-rds"
  description = "Mass RDS DB subnet group"
  subnet_ids  = var.vpc_app_subnet_ids
}

resource "aws_db_instance" "default" {
  identifier = "massgov-pfml-${var.environment_name}"

  engine            = "postgres"
  engine_version    = var.postgres_version
  instance_class    = "db.t2.small"
  allocated_storage = 5
  storage_encrypted = true

  name     = "massgov_pfml_${var.environment_name}"
  username = "pfml"
  password = data.aws_ssm_parameter.db_password.value
  port     = "5432"

  auto_minor_version_upgrade  = false # disallow to avoid unexpected downtime
  allow_major_version_upgrade = false # disallow by default to avoid unexpected downtime
  apply_immediately           = true  # enact changes immediately instead of waiting for a "maintenance window"
  copy_tags_to_snapshot       = true  # not applicable right now, but useful in the future

  db_subnet_group_name = aws_db_subnet_group.rds_postgres.name

  lifecycle {
    prevent_destroy = true # disallow by default to avoid unexpected data loss
  }
}
