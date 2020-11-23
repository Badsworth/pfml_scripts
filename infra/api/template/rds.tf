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

resource "aws_db_subnet_group" "rds_postgres_dbprivate" {
  name        = "${local.app_name}-${var.environment_name}-rds"
  description = "Mass RDS DB subnet group"
  subnet_ids  = var.vpc_db_subnet_ids
}

resource "aws_db_parameter_group" "postgres11" {
  name_prefix = "${local.app_name}-${var.environment_name}-${var.postgres_parameter_group_family}-"
  family      = var.postgres_parameter_group_family
  description = "PSQL 11 RDS parameters for ${local.app_name}-${var.environment_name}"

  # Log all client connection details.
  #
  # This can help determine the source, username, frequency,
  # and time of various connections.
  parameter {
    name  = "log_connections"
    value = 1
  }

  # Log all client disconnection details.
  #
  # This can help to determine how long a client was connected.
  parameter {
    name  = "log_disconnections"
    value = 1
  }

  # Log all DDL (schema-change-related) statements.
  #
  # This helps in identifying when changes were made,
  # including any unexpected changes.
  parameter {
    name  = "log_statement"
    value = "ddl"
  }
  # Error verbosity: TERSE excludes the logging of DETAIL, HINT, QUERY and CONTEXT information
  parameter {
    name  = "log_error_verbosity"
    value = "terse"
  }
}

resource "aws_db_instance" "default" {
  identifier = "massgov-pfml-${var.environment_name}"

  engine                              = "postgres"
  engine_version                      = var.postgres_version
  instance_class                      = var.db_instance_class
  allocated_storage                   = var.db_allocated_storage
  max_allocated_storage               = var.db_max_allocated_storage
  storage_type                        = var.db_storage_type
  iops                                = var.db_iops
  storage_encrypted                   = true
  multi_az                            = var.db_multi_az
  iam_database_authentication_enabled = true

  name     = "massgov_pfml_${var.environment_name}"
  username = "pfml"
  password = aws_ssm_parameter.db_password.value
  port     = "5432"

  vpc_security_group_ids = [aws_security_group.rds_postgresql.id]

  backup_retention_period   = 35
  skip_final_snapshot       = false
  final_snapshot_identifier = "massgov-pfml-${var.environment_name}-final-snapshot"

  auto_minor_version_upgrade  = false # disallow to avoid unexpected downtime
  allow_major_version_upgrade = false # disallow by default to avoid unexpected downtime
  apply_immediately           = true  # enact changes immediately instead of waiting for a "maintenance window"
  copy_tags_to_snapshot       = true  # not applicable right now, but useful in the future

  # Require this flag to be manually turned off before deleting the DB;
  # This is required by Smartronix CIS Benchmark audits, which are run via AWS Config through their CAMS Monitoring Harness.
  deletion_protection = true

  db_subnet_group_name = aws_db_subnet_group.rds_postgres_dbprivate.name
  parameter_group_name = aws_db_parameter_group.postgres11.name

  monitoring_interval = 30
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn
  // Note: `performance_insights_enabled` creates the RDSOSMetrics log group which is
  //       shared across the whole AWS account (used for all environments)
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  lifecycle {
    prevent_destroy = true # disallow by default to avoid unexpected data loss
  }

  tags = merge(module.constants.common_tags, {
    "SMX:Asset"   = "v1:massgov_pfml_${var.environment_name}:${module.constants.smartronix_environment_tags[var.environment_name]}:RDS:PFML:Advanced:None"
    environment   = module.constants.environment_tags[var.environment_name]
    Name          = "massgov_pfml_${var.environment_name}"
    backup        = var.environment_name == "prod" ? "prod" : "nonprod"
    "Patch Group" = var.environment_name == "prod" ? "prod-linux1" : "nonprod-linux1"
    schedulev2    = var.environment_name == "test" ? "0700_2400_weekdays" : "na"
    # schedulev2 is an EOTSS-required custom tag. It configures a mandatory scheduled downtime
    # period for test only.
    #
    # If you change this schedule, please update the ECS autoscaling policy in app_autoscaling.tf.
    #
    # See https://lwd.atlassian.net/wiki/spaces/DD/pages/275611773/RDS+databases.
  })
}
