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
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

# Subnet group managed by Smartronix
data "aws_db_subnet_group" "rds_postgres_dbprivate" {
  name = "eolwd-pfml-${var.environment_name == "prod" ? "prod" : "nonprod"}-dbprivate"
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
  enabled_cloudwatch_logs_exports     = ["postgresql", "upgrade"]

  depends_on = [
    aws_cloudwatch_log_group.postgresql
  ]

  name     = replace("massgov_pfml_${var.environment_name}", "-", "_")
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

  db_subnet_group_name = data.aws_db_subnet_group.rds_postgres_dbprivate.name
  parameter_group_name = var.environment_name == "prod" ? "pfml-postgres12-prod" : "pfml-postgres12-non-prod"

  monitoring_interval = 30
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn
  // Note: `performance_insights_enabled` creates the RDSOSMetrics log group which is
  //       shared across the whole AWS account (used for all environments)
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  lifecycle {
    prevent_destroy = true # disallow by default to avoid unexpected data loss
    ignore_changes = [
      #-----------------forces configuration in AWS Console--------------------#
      # 
      # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.DBInstance.Status.html 
      #
      # Changes to "instance_class" and "storage_type" cause a lock on 
      # further configuration changes to be imposed by AWS while the db instance 
      # goes into "storage-optimization" status, which can last anywhere from 
      # minutes to hours. Plan changes to these configs with this in mind, and
      # any changes must be made in AWS Console first, then in Terraform as a follow-up.
      # 
      # "engine_version", "parameter_group_name" and "db_subnet_group_name"  will be managed manually by Smartronix
      # -----------------------------------------------------------------------#
      db_subnet_group_name,
      engine_version,
      instance_class,
      storage_type,
      parameter_group_name
    ]
  }

  tags = merge(module.constants.common_tags, {
    # Required tags
    "SMX:Asset"   = "v1:massgov_pfml_${var.environment_name}:${module.constants.smartronix_environment_tags[var.environment_name]}:RDS:PFML:Advanced:None"
    environment   = module.constants.environment_tags[var.environment_name]
    Name          = "massgov_pfml_${var.environment_name}"
    backup        = var.environment_name == "prod" ? "prod" : "nonprod"
    "Patch Group" = var.environment_name == "prod" ? "prod-linux1" : "nonprod-linux1"

    # Scheduler tag for operations team (smartronix)
    "Scheduler" = var.environment_name == "training" ? "_office-hours-db" : ""

    # Human-readable tag for operations team (smartronix)
    purpose = "${var.environment_name} database for PFML"

    # schedulev2 is an EOTSS-required custom tag. It configures a mandatory scheduled downtime
    # period for test only.*
    #
    # *Test downtime is currently disabled to account for launch activities. Usually this requires an exception tag provided by EOTSS,
    #  however a separate arrangement has been made as indicated in ServiceNow ticket SCTASK0208809.
    #
    # If you change this schedule, please update the ECS autoscaling policy in autoscaling-ecs.tf.
    #
    # See https://lwd.atlassian.net/wiki/spaces/DD/pages/275611773/RDS+databases.
    schedulev2 = "na"
  })
}
# ------------------------------------
# Cloudwatch log group for RDS
resource "aws_cloudwatch_log_group" "postgresql" {
  name = "/aws/rds/instance/massgov-pfml-${var.environment_name}/postgresql"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
  # number of days to keep log events. Default is 0, which is forever
  retention_in_days = 0
}
