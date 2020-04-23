# Setup an RDS Postgres DB for API environments
#
# See https://lwd.atlassian.net/wiki/spaces/DD/pages/275611773/RDS+databases

# Why is DB identifier using hyphens and name using underscore?
# https://github.com/hashicorp/terraform/issues/16784
# https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html#RDS_Limits.Constraints

# Note: This password is stored in tfstate but not shown in regular terraform commands.
#       Even if it was stored manually in SSM Parameter Store and pulled down,
#       the secret value would be visible in the tfstate.
resource "random_password" "rds_super_password" {
  length           = 48
  special          = true
  min_special      = 6
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/service/${local.app_name}/${var.environment_name}/db-password"
  type  = "SecureString"
  value = random_password.rds_super_password.result
}

resource "aws_db_subnet_group" "rds_postgres" {
  name        = "massgov-pfml-${var.environment_name}-rds"
  description = "Mass RDS DB subnet group"
  subnet_ids  = var.vpc_app_subnet_ids
}

resource "aws_db_instance" "default" {
  identifier = "massgov-pfml-${var.environment_name}"

  engine                = "postgres"
  engine_version        = var.postgres_version
  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = var.db_storage_type
  iops                  = var.db_iops
  storage_encrypted     = true
  multi_az              = var.db_multi_az

  name     = "massgov_pfml_${var.environment_name}"
  username = "pfml"
  password = aws_ssm_parameter.db_password.value
  port     = "5432"

  backup_retention_period   = 35
  skip_final_snapshot       = false
  final_snapshot_identifier = "massgov-pfml-${var.environment_name}-final-snapshot"

  auto_minor_version_upgrade  = false # disallow to avoid unexpected downtime
  allow_major_version_upgrade = false # disallow by default to avoid unexpected downtime
  apply_immediately           = true  # enact changes immediately instead of waiting for a "maintenance window"
  copy_tags_to_snapshot       = true  # not applicable right now, but useful in the future

  db_subnet_group_name = aws_db_subnet_group.rds_postgres.name

  monitoring_interval                   = 30
  monitoring_role_arn                   = aws_iam_role.rds_enhanced_monitoring.arn
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  lifecycle {
    prevent_destroy = true # disallow by default to avoid unexpected data loss
  }

  tags = {
    agency        = "eol"
    application   = "coreinf"
    businessowner = "kevin.yeh@mass.gov"
    createdby     = "kevin.yeh@mass.gov"
    environment   = var.environment_name
    itowner       = "kevin.yeh@mass.gov"
    secretariat   = "eolwd"
    Name          = "massgov_pfml_${var.environment_name}"
    backup        = "nonprod"
    "Patch Group" = "nonprod-linux1"
    schedulev2    = "0700_2400_weekdays"
  }
}
