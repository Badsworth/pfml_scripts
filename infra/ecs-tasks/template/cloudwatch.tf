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
# Run register-leave-admins-with-fineos every 15 minutes.
module "register_leave_admins_with_fineos_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_register_admins_job

  task_name           = "register-leave-admins-with-fineos"
  schedule_expression = "rate(15 minutes)"
  environment_name    = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["register-leave-admins-with-fineos"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["register-leave-admins-with-fineos"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.register_admins_task_role.arn
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Run fineos-bucket-tool daily at 3am EST (4am EDT) (8am UTC)
module "fineos_bucket_tool_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name           = "fineos-data-export-tool"
  schedule_expression = "cron(0 8 * * ? *)"
  environment_name    = var.environment_name

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
# run at 3:30pm EST (4:30pm EDT) (8:30pm UTC) and 6:30pm EST (7:30pm EDT) (11:30pm UTC)
module "fineos_extract_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name           = "fineos-report-extracts-tool"
  schedule_expression = "cron(30 20,23 * * ? *)"
  environment_name    = var.environment_name

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

  task_name           = "import-fineos-to-warehouse"
  schedule_expression = "cron(0 3 * * ? *)"
  environment_name    = var.environment_name

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

  task_name           = "fineos-error-extract-tool"
  schedule_expression = "cron(0 13 * * ? *)"
  environment_name    = var.environment_name

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

  task_name           = "export-leave-admins-created"
  schedule_expression = "rate(24 hours)"
  environment_name    = var.environment_name

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
# Run cps-errors daily at 9am EST (10am EDT) (2pm UTC)
# This needs to run after fineos-bucket-tool
module "cps_errors_crawler_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = true

  task_name           = "cps_errors_crawler"
  schedule_expression = "cron(0 14 * * ? *)"
  environment_name    = var.environment_name

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

  task_name           = "reductions-dia-send-claimant-lists"
  schedule_expression = "cron(0 8 ? * MON-FRI *)"
  environment_name    = var.environment_name

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

  task_name           = "reductions-dua-send-claimant-lists"
  schedule_expression = "cron(0 8 * * ? *)"
  environment_name    = var.environment_name

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

  task_name           = "reductions-process-agency-data"
  schedule_expression = "cron(0/15 8-23,0 * * ? *)"
  environment_name    = var.environment_name

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

  task_name           = "pub-payments-process-fineos"
  schedule_expression = "cron(0 3 ? * MON-FRI *)"
  environment_name    = var.environment_name

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

  task_name           = "weekend-pub-claimant-extract"
  schedule_expression = "cron(0 10 ? * SAT-SUN *)"
  environment_name    = var.environment_name

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
          "--steps=claimant-extract"
        ]
      }
    ]
  }
  JSON
}

## NOTE: If you are adding a new scheduled event here, please add monitoring by including it
#        in the list in infra/modules/alarms_api/alarms-aws.tf.
