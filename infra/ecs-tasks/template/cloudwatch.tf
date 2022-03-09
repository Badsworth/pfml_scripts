# This file sets up the centralized cloudwatch log group for ECS tasks.
#
# All logs for background ECS tasks are sent to the same log group and forwarded to New Relic through the lambda forwarder.
#
# Additionally, recurring task schedules are configured here using the ecs_task_scheduler module.
#
# ## NOTE: If you are adding a new scheduled event here, please add monitoring by including it
#          in the list in infra/modules/alarms_api/alarms-aws.tf.

data "aws_ecs_cluster" "cluster" { cluster_name = var.environment_name }

# Cloudwatch log group to for streaming ECS application logs.
resource "aws_cloudwatch_log_group" "ecs_tasks" {
  name = "service/${local.app_name}-${var.environment_name}/ecs-tasks"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

locals {
  # This ARN describes a 3rd-party lambda installed outside of Terraform thru the AWS Serverless Application Repository.
  # This lambda ingests CloudWatch logs from several sources, and packages them for transmission to New Relic's servers.
  # This lambda was modified post-installation to fix an apparent bug in the processing/packaging of its telemetry data.
  newrelic_log_ingestion_lambda = module.constants.newrelic_log_ingestion_arn
  fineos_error_extract_prefixes = [
    "EmployeeFileError"
  ]
}

resource "aws_cloudwatch_log_subscription_filter" "ecs_task_logging" {
  name            = "ecs_task_logs"
  log_group_name  = aws_cloudwatch_log_group.ecs_tasks.name
  destination_arn = local.newrelic_log_ingestion_lambda
  # matches all log events
  filter_pattern = ""
}

resource "aws_lambda_permission" "ecs_permission_tasks_logging" {
  statement_id  = "NRLambdaPermission_ECSTasksLogging_${var.environment_name}"
  action        = "lambda:InvokeFunction"
  function_name = local.newrelic_log_ingestion_lambda
  principal     = "logs.us-east-1.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
}

# ----------------------------------------------------------------------------------------------
# Scheduled tasks


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run fineos-bucket-tool daily at 3am EST (4am EDT) (8am UTC)
module "fineos_bucket_tool_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "fineos-data-export-tool"
  schedule_expression_standard         = "cron(0 9 * * ? *)"
  schedule_expression_daylight_savings = "cron(0 8 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_bucket_tool_role.arn

  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "fineos-bucket-tool",
        "command": [
          "fineos-bucket-tool",
          "--recursive",
          "--dated-folders",
          "--copy_dir", "${var.fineos_data_export_path}",
          "--to_dir", "s3://${data.aws_s3_bucket.business_intelligence_tool.bucket}/fineos/dataexports",
          "--file_prefixes", "all"
        ]
      }
    ]
  }
  JSON
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# run at 12:30pm EST (1:30pm EDT) (5:30pm UTC) and 4:30pm EST (5:30pm EDT) (9:30pm UTC)
module "fineos_extract_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "fineos-report-extracts-tool"
  schedule_expression_standard         = "cron(30 17,21 * * ? *)"
  schedule_expression_daylight_savings = "cron(30 16,20 * * ? *)"

  environment_name = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_bucket_tool_role.arn

  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "fineos-bucket-tool",
        "command": [
          "fineos-bucket-tool",
          "--recursive",
          "--dated-folders",
          "--copy_dir", "${var.fineos_report_export_path}",
          "--to_dir", "s3://${data.aws_s3_bucket.business_intelligence_tool.bucket}/fineos/dataexports",
          "--file_prefixes", "all"
        ]
      }
    ]
  }
  JSON
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run import-fineos-to-warehouse at 10pm EST (11pm EDT) (3am UTC +1 day)
module "import_fineos_to_warehouse" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "import-fineos-to-warehouse"
  schedule_expression_standard         = "cron(0 4 * * ? *)"
  schedule_expression_daylight_savings = "cron(0 3 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["import-fineos-to-warehouse"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["import-fineos-to-warehouse"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_bucket_tool_role.arn
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run fineos-bucket-tool daily at 8am EST (9am EDT) (1pm UTC)
module "fineos_error_extract_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "fineos-error-extract-tool"
  schedule_expression_standard         = "cron(0 14 * * ? *)"
  schedule_expression_daylight_savings = "cron(0 13 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_bucket_tool_role.arn

  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "fineos-bucket-tool",
        "command": [
          "fineos-bucket-tool",
          "--recursive",
          "--dated-folders",
          "--copy_dir", "${var.fineos_error_export_path}",
          "--to_dir", "s3://${data.aws_s3_bucket.agency_transfer.bucket}/cps-errors/received/",
          "--archive_dir", "s3://${data.aws_s3_bucket.agency_transfer.bucket}/cps-errors/processed/",
          "--file_prefixes", "all"
        ]
      }
    ]
  }
  JSON
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run execute-sql daily to export a report to S3 of leave admins created
module "export_leave_admins_created_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "export-leave-admins-created"
  schedule_expression_standard         = "rate(24 hours)"
  schedule_expression_daylight_savings = "rate(24 hours)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["execute-sql"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["execute-sql"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.task_execute_sql_task_role.arn

  input = <<DOC
  {
  "containerOverrides": [
          {
            "name": "execute-sql",
            "command": [
              "execute-sql",
              "--s3_output=api_db/accounts_created",
              "--s3_bucket=massgov-pfml-${var.environment_name}-business-intelligence-tool",
              "--use_date",
              "SELECT pu.email_address as email, pu.user_id as user_id, pu.sub_id as cognito_id,ula.fineos_web_id as fineos_id,e.employer_name as employer_name,e.employer_dba as employer_dba,e.employer_fein as fein,e.fineos_employer_id as fineos_customer_number,ula.created_at as date_created FROM public.user pu LEFT JOIN link_user_leave_administrator ula ON (pu.user_id=ula.user_id) LEFT JOIN employer e ON (ula.employer_id=e.employer_id) WHERE ula.created_at >= now() - interval '24 hour'"
            ]
          }
        ]
  }
  DOC
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Runs daily at 7am EST (8am EDT) (12pm UTC)
# Run execute-sql daily to export a report to S3 of applications that have completed part 3 but aren't ID proofed
module "export_psd_report_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "export-psd-report"
  schedule_expression_standard         = "cron(0 13 * * ? *)"
  schedule_expression_daylight_savings = "cron(0 12 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["execute-sql"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["execute-sql"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.task_execute_sql_task_role.arn

  input = <<DOC
  {
  "containerOverrides": [
          {
            "name": "execute-sql",
            "command": [
              "execute-sql",
              "--s3_output=dfml-reports/applications_passed_part_3",
              "--s3_bucket=massgov-pfml-${var.environment_name}-reports",
              "select claim_id, fineos_absence_id, updated_at FROM claim where claim_id in (select claim_id from application where completed_time is not null and completed_time > CURRENT_DATE - 1) and (is_id_proofed = false or is_id_proofed is null)"
            ]
          }
        ]
  }
  DOC
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run cps-errors daily at 9am EST (10am EDT) (2pm UTC)
# This needs to run after fineos-bucket-tool
module "cps_errors_crawler_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "cps_errors_crawler"
  schedule_expression_standard         = "cron(0 15 * * ? *)"
  schedule_expression_daylight_savings = "cron(0 14 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["cps-errors-crawler"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["cps-errors-crawler"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.cps_errors_crawler_task_role.arn
}

module "reductions_dia_send_claimant_lists_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_reductions_send_claimant_lists_to_agencies_schedule

  task_name                            = "reductions-dia-send-claimant-lists"
  schedule_expression_standard         = "cron(0 9 ? * MON-FRI *)"
  schedule_expression_daylight_savings = "cron(0 8 ? * MON-FRI *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["reductions-send-claimant-lists"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["reductions-send-claimant-lists"].family
  ecs_task_executor_role     = aws_iam_role.reductions_workflow_execution_role.arn
  ecs_task_role              = aws_iam_role.reductions_workflow_task_role.arn

  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "reductions-send-claimant-lists",
        "command": [
          "reductions-send-claimant-lists-to-agencies",
          "--steps=DIA"
        ]
      }
    ]
  }
  JSON
}

module "reductions_dua_send_claimant_lists_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_reductions_send_claimant_lists_to_agencies_schedule

  task_name                            = "reductions-dua-send-claimant-lists"
  schedule_expression_standard         = "cron(0 9 * * ? *)"
  schedule_expression_daylight_savings = "cron(0 8 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["reductions-send-claimant-lists"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["reductions-send-claimant-lists"].family
  ecs_task_executor_role     = aws_iam_role.reductions_workflow_execution_role.arn
  ecs_task_role              = aws_iam_role.reductions_workflow_task_role.arn

  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "reductions-send-claimant-lists",
        "command": [
          "reductions-send-claimant-lists-to-agencies",
          "--steps=DUA"
        ]
      }
    ]
  }
  JSON
}

module "reductions_process_agency_data_lists_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_reductions_process_agency_data_schedule

  task_name = "reductions-process-agency-data"
  # Every 15 minutes between 4 AM - 10 PM Eastern
  schedule_expression_standard         = "cron(0/15 0-2,3,9-23 * * ? *)"
  schedule_expression_daylight_savings = "cron(0/15 0-1,2,8-23 * * ? *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["reductions-process-agency-data"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["reductions-process-agency-data"].family
  ecs_task_executor_role     = aws_iam_role.reductions_workflow_execution_role.arn
  ecs_task_role              = aws_iam_role.reductions_workflow_task_role.arn
}

# Run pub-payments-process-fineos at 10pm EST (11pm EDT) Sunday through Thursday
# The output files will be available by the start of business Mon-Fri
module "pub-payments-process-fineos" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_pub_automation_fineos

  task_name                            = "pub-payments-process-fineos"
  schedule_expression_standard         = "cron(0 4 ? * MON-FRI *)"
  schedule_expression_daylight_savings = "cron(0 3 ? * MON-FRI *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["pub-payments-process-fineos"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-payments-process-fineos"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.pub_payments_process_fineos_task_role.arn
}

# Run pub-payments-process-fineos claimant extract only
# at 6am EST (7am EDT) Saturday/Sunday (For Friday/Saturday extract)
# Runs at 6am instead of 11pm to avoid monthly saturday DB downtime
module "weekend-pub-payments-process-fineos" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_pub_automation_fineos

  task_name                            = "weekend-pub-claimant-extract"
  schedule_expression_standard         = "cron(0 11 ? * SAT-SUN *)"
  schedule_expression_daylight_savings = "cron(0 10 ? * SAT-SUN *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["pub-payments-process-fineos"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-payments-process-fineos"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.pub_payments_process_fineos_task_role.arn

  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "pub-payments-process-fineos",
        "command": [
          "pub-payments-process-fineos",
          "--steps", "consume-fineos-claimant", "claimant-extract", "consume_fineos_1099_request","do_1099_data_extract"
        ]
      }
    ]
  }
  JSON
}

# Run fineos-import-la-units task prior to pub-payments-process-fineos
# 10PM EST
module "fineos-import-la-units" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "fineos-import-la-units"
  schedule_expression_standard         = "cron(0 3 ? * MON-FRI *)"
  schedule_expression_daylight_savings = "cron(0 2 ? * MON-FRI *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-import-la-units"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-import-la-units"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_import_la_org_units_task_role.arn
}

# Run fineos-import-la-units task prior to pub-payments-process-fineos
# Weekends only - 5AM EST - keeping consistent with weekend-pub-payments-process-fineos to avoid DB maintenance
module "weekend-fineos-import-la-units" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "weekend-fineos-import-la-units"
  schedule_expression_standard         = "cron(0 10 ? * SAT-SUN *)"
  schedule_expression_daylight_savings = "cron(0 9 ? * SAT-SUN *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-import-la-units"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-import-la-units"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_import_la_org_units_task_role.arn
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Trigger full payment snapshot extracts
# Run fineos-bucket-tool every week on Wednesday at 7 am UTC, 2am EST, 3am EDT
module "fineos_snapshot_extract_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name                            = "fineos-snapshot-extracts-tool"
  schedule_expression_standard         = "cron(0 8 ? * 4 *)"
  schedule_expression_daylight_savings = "cron(0 7 ? * 4 *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-bucket-tool"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.fineos_bucket_tool_role.arn


  input = <<JSON
  {
    "containerOverrides": [
      {
        "name": "fineos-bucket-tool",
        "command": [
          "fineos-bucket-tool",
          "--copy", "s3://${data.aws_s3_bucket.agency_transfer.bucket}/payments/static/fineos-query/config-fineos-payments-snapshot.json",
          "--to", "${var.fineos_adhoc_data_export_path}/config/config.json"
        ]
      }
    ]
  }
  JSON
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Process full payment snapshot extracts.
# The task will process extract files generated by fineos_snapshot_extract_scheduler above.
# Run fineos-bucket-tool every week on Wednesday at 10 am UTC, 5am EST, 6am EDT
module "pub-payments-process-snapshot" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_pub_automation_fineos

  task_name                            = "pub-payments-process-snapshot"
  schedule_expression_standard         = "cron(0 11 ? * 4 *)"
  schedule_expression_daylight_savings = "cron(0 10 ? * 4 *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["pub-payments-process-snapshot"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-payments-process-snapshot"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.pub_payments_process_fineos_task_role.arn
}


module "pub-payments-copy-audit-report-scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_pub_payments_copy_audit_report_schedule

  task_name = "pub-payments-copy-audit-report"
  # Every day at 4am ET (9am UTC)
  schedule_expression_standard         = "cron(0 9 ? * MON-FRI *)"
  schedule_expression_daylight_savings = "cron(0 8 ? * MON-FRI *)"
  environment_name                     = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["pub-payments-copy-audit-report"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-payments-copy-audit-report"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.pub_payments_copy_audit_report_task_role.arn
}

# TODO uncomment when ready
# The task will process fineos extract files for IAWW data.
# Run fineos-import-iaww at 3am EST (4am EDT) Monday through Friday

# module "fineos-import-iaww" {
#   source     = "../../modules/ecs_task_scheduler"
#   is_enabled = var.enable_pub_automation_fineos

#   task_name                            = "fineos-import-iaww"
#   schedule_expression_standard         = "cron(0 8 ? * MON-FRI *)"
#   schedule_expression_daylight_savings = "cron(0 7 ? * MON-FRI *)"
#   environment_name                     = var.environment_name

#   cluster_arn        = data.aws_ecs_cluster.cluster.arn
#   app_subnet_ids     = var.app_subnet_ids
#   security_group_ids = [aws_security_group.tasks.id]

#   ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["fineos-import-iaww"].arn
#   ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["fineos-import-iaww"].family
#   ecs_task_executor_role     = aws_iam_role.task_executor.arn
#   ecs_task_role              = aws_iam_role.fineos_import_iaww_task_role.arn
# }

# Run 1099-form-generator at <Every 3 hours Mon-Fri>
# Defined in /pfml/infra/ecs_tasks/template/tasks_1099.tf
# module "pub-payments-process-1099-form-generator" {
#   source     = "../../modules/ecs_task_scheduler"
#   is_enabled = true

#   task_name           = "1099-form-generator"
#   schedule_expression_standard = "cron(0 3 ? * MON-FRI *)"
#   schedule_expression_daylight_savings = "cron(0 2 ? * MON-FRI *)"
#   environment_name    = var.environment_name

#   cluster_arn        = data.aws_ecs_cluster.cluster.arn
#   app_subnet_ids     = var.app_subnet_ids
#   security_group_ids = [aws_security_group.tasks.id]

#   ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks_1099.arn
#   ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks_1099.family
#   ecs_task_executor_role     = aws_iam_role.task_executor.arn
#   ecs_task_role              = aws_iam_role.pub_payments_process_fineos_task_role.arn
# }

# TODO uncomment if this is ever to be scheduled.  Adjust schedule_expression accordingly
# Run pub-claimant-address-validation at <schedule is TBD>
# 
# module "pub-claimant-address-validation" {
#   source     = "../../modules/ecs_task_scheduler"
#   is_enabled = var.enable_pub_automation_claimant_address_validation

#   task_name           = "pub-claimant-address-validation"
#   schedule_expression = "cron(0 3 ? * MON-FRI *)"
#   environment_name    = var.environment_name

#   cluster_arn        = data.aws_ecs_cluster.cluster.arn
#   app_subnet_ids     = var.app_subnet_ids
#   security_group_ids = [aws_security_group.tasks.id]

#   ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["pub-claimant-address-validation"].arn
#   ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-claimant-address-validation"].family
#   ecs_task_executor_role     = aws_iam_role.task_executor.arn
#   ecs_task_role              = aws_iam_role.pub_payments_process_fineos_task_role.arn
# }

## NOTE: If you are adding a new scheduled event here, please add monitoring by including it
#        in the list in infra/modules/alarms_api/alarms-aws.tf.
