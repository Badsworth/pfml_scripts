# Templating and configurations for ECS tasks.
#
# If you need to add a new ECS task, add it to the locals.tasks variable
# in the following format:
#
# "${local.app_name}-your-task-name" = {
#   command = ["the-command-name"],
#   task_role = null
# }
#
# The command name usually comes from pyproject.toml.
#
# The task_role should be defined, but can be null if your running task does not need
# to be assigned an IAM role for additional permissions to AWS resources.
# If not null, it should have a task_role_arn stored in it for the aws_ecs_task_definition.
#
# CPU and memory defaults are 512 (CPU units) and 1024 (MB).
# If you need more resources than this, add "cpu" or "memory" keys to your ECS task's
# entry in locals.tasks. The defaults will be used if these keys are absent.
#
# Once this is done, apply your terraform changes and test your new ECS task in the test environment.
#
# From the root of the git repository (example):
#
# ./bin/run-ecs-task/run-task.sh test db-migrate-up kevin.yeh
#
locals {
  tasks = {
    "db-migrate-up" = {
      command = ["db-migrate-up"]
    },

    "db-migrate-down" = {
      command = ["db-migrate-down"]
    }

    "db-admin-create-db-users" = {
      command             = ["db-admin-create-db-users"],
      containers_template = "db_admin_create_db_users.json"
    },

    "db-create-fineos-user" = {
      command = ["db-create-fineos-user"]
    },

    "execute-sql" = {
      command             = ["execute-sql"]
      containers_template = "execute_sql_template.json"
      task_role           = aws_iam_role.task_execute_sql_task_role.arn
      vars = {
        s3_export_bucket = "massgov-pfml-${var.environment_name}-execute-sql-export"
      }
    },

    "bulk-user-import" = {
      command             = ["bulk-user-import"]
      containers_template = "bulk_user_import_template.json"
      task_role           = aws_iam_role.task_bulk_import_task_role.arn
      vars = {
        fineos_client_integration_services_api_url = var.fineos_client_integration_services_api_url
        fineos_client_customer_api_url             = var.fineos_client_customer_api_url
        fineos_client_group_client_api_url         = var.fineos_client_group_client_api_url
        fineos_client_wscomposer_api_url           = var.fineos_client_wscomposer_api_url
        fineos_client_wscomposer_user_id           = var.fineos_client_wscomposer_user_id
        fineos_client_oauth2_url                   = var.fineos_client_oauth2_url
        fineos_client_oauth2_client_id             = var.fineos_client_oauth2_client_id
        cognito_user_pool_id                       = var.cognito_user_pool_id
        process_csv_data_bucket_name               = aws_s3_bucket.bulk_user_import.bucket # massgov-pfml-${environment_name}-bulk-user-import
      }
    },

    "dor-import" = {
      command             = ["dor-import"],
      task_role           = aws_iam_role.dor_import_task_role.arn,
      execution_role      = aws_iam_role.dor_import_execution_role.arn,
      cpu                 = "4096",
      memory              = "18432",
      containers_template = "dor_import_template.json"
    },

    "fineos-import-employee-updates" = {
      command             = ["fineos-import-employee-updates"]
      task_role           = aws_iam_role.fineos_import_employee_updates_task_role.arn
      cpu                 = "2048"
      memory              = "9216"
      containers_template = "fineos_import_employee_updates_template.json"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id
        input_directory_path            = var.fineos_import_employee_updates_input_directory_path
      }
    },

    "register-leave-admins-with-fineos" = {
      command             = ["register-leave-admins-with-fineos"]
      task_role           = aws_iam_role.register_admins_task_role.arn,
      cpu                 = "4096",
      memory              = "18432",
      containers_template = "register_leave_admins_with_fineos.json"
      vars = {
        fineos_client_integration_services_api_url = var.fineos_client_integration_services_api_url
        fineos_client_customer_api_url             = var.fineos_client_customer_api_url
        fineos_client_group_client_api_url         = var.fineos_client_group_client_api_url
        fineos_client_wscomposer_api_url           = var.fineos_client_wscomposer_api_url
        fineos_client_wscomposer_user_id           = var.fineos_client_wscomposer_user_id
        fineos_client_oauth2_url                   = var.fineos_client_oauth2_url
        fineos_client_oauth2_client_id             = var.fineos_client_oauth2_client_id
      }
    }

    "load-employers-to-fineos" = {
      command             = ["load-employers-to-fineos"]
      containers_template = "load_employers_to_fineos_template.json"
      vars = {
        fineos_client_integration_services_api_url = var.fineos_client_integration_services_api_url
        fineos_client_customer_api_url             = var.fineos_client_customer_api_url
        fineos_client_group_client_api_url         = var.fineos_client_group_client_api_url
        fineos_client_wscomposer_api_url           = var.fineos_client_wscomposer_api_url
        fineos_client_wscomposer_user_id           = var.fineos_client_wscomposer_user_id
        fineos_client_oauth2_url                   = var.fineos_client_oauth2_url
        fineos_client_oauth2_client_id             = var.fineos_client_oauth2_client_id
      }
    },

    "reductions-retrieve-payment-lists" = {
      command             = ["reductions-retrieve-payment-lists-from-agencies"]
      containers_template = "reductions_retrieve_payment_lists_from_agencies.json"
      task_role           = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow"
      execution_role      = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-wrkflw-execution-role"
      vars = {
        eolwd_moveit_sftp_uri = var.eolwd_moveit_sftp_uri
      }
    },

    "reductions-send-claimant-lists" = {
      command             = ["reductions-send-claimant-lists-to-agencies"]
      containers_template = "reductions_send_claimant_lists_to_agencies.json"
      task_role           = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow"
      execution_role      = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-wrkflw-execution-role"
      vars = {
        eolwd_moveit_sftp_uri = var.eolwd_moveit_sftp_uri
      }
    },

    "reductions-send-wage-replacement" = {
      command             = ["reductions-send-wage-replacement-payments-to-dfml"]
      containers_template = "reductions_send_wage_replacement_payments_to_dfml.json"
      task_role           = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow"
      execution_role      = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-wrkflw-execution-role"
      vars = {
        agency_reductions_email_address = var.agency_reductions_email_address
      }
    },

    "pub-payments-create-pub-files" = {
      command             = ["pub-payments-create-pub-files"]
      containers_template = "pub_payments_create_pub_files_template.json"
      task_role           = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-pub-payments-create-pub-files"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        fineos_data_import_path = var.fineos_data_import_path
        fineos_data_export_path = var.fineos_data_export_path
      }
    },

    "pub-payments-process-pub-returns" = {
      command             = ["pub-payments-process-pub-returns"]
      containers_template = "pub_payments_process_pub_returns_template.json"
      task_role           = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-pub-payments-process-pub-returns"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        fineos_data_import_path = var.fineos_data_import_path
      }
    },

    "fineos-eligibility-feed-export" = {
      command             = ["fineos-eligibility-feed-export"]
      containers_template = "fineos_eligibility_feed_export_template.json"
      task_role           = aws_iam_role.fineos_eligibility_feed_export_task_role.arn
      cpu                 = "4096"
      memory              = "8192"
      vars = {
        fineos_client_integration_services_api_url = var.fineos_client_integration_services_api_url
        fineos_client_customer_api_url             = var.fineos_client_customer_api_url
        fineos_client_group_client_api_url         = var.fineos_client_group_client_api_url
        fineos_client_wscomposer_api_url           = var.fineos_client_wscomposer_api_url
        fineos_client_wscomposer_user_id           = var.fineos_client_wscomposer_user_id
        fineos_client_oauth2_url                   = var.fineos_client_oauth2_url
        fineos_client_oauth2_client_id             = var.fineos_client_oauth2_client_id

        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        output_directory_path = var.fineos_eligibility_feed_output_directory_path
      }
    }

    "payments-ctr-process" = {
      command             = ["payments-ctr-process"]
      containers_template = "payments_ctr_process_template.json"
      task_role           = aws_iam_role.payments_ctr_process_task_role.arn
      execution_role      = aws_iam_role.payments_ctr_import_execution_role.arn
      cpu                 = "2048"
      memory              = "16384"
      vars = {
        eolwd_moveit_sftp_uri    = var.eolwd_moveit_sftp_uri
        ctr_moveit_incoming_path = var.ctr_moveit_incoming_path
        ctr_moveit_archive_path  = var.ctr_moveit_archive_path
        ctr_moveit_outgoing_path = var.ctr_moveit_outgoing_path
        pfml_ctr_inbound_path    = var.pfml_ctr_inbound_path
        pfml_ctr_outbound_path   = var.pfml_ctr_outbound_path
        pfml_error_reports_path  = var.pfml_error_reports_path

        dfml_project_manager_email_address     = var.dfml_project_manager_email_address
        pfml_email_address                     = var.pfml_email_address
        ctr_gax_bievnt_email_address           = var.ctr_gax_bievnt_email_address
        ctr_vcc_bievnt_email_address           = var.ctr_vcc_bievnt_email_address
        dfml_business_operations_email_address = var.dfml_business_operations_email_address

        ctr_data_mart_host     = var.ctr_data_mart_host
        ctr_data_mart_username = var.ctr_data_mart_username
      }
    },

    "payments-fineos-process" = {
      command             = ["payments-fineos-process"]
      containers_template = "payments_fineos_process_template.json"
      task_role           = aws_iam_role.payments_fineos_process_task_role.arn
      cpu                 = "2048"
      memory              = "16384"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        fineos_data_export_path   = var.fineos_data_export_path
        fineos_data_import_path   = var.fineos_data_import_path
        pfml_fineos_inbound_path  = var.pfml_fineos_inbound_path
        pfml_fineos_outbound_path = var.pfml_fineos_outbound_path
        pfml_error_reports_path   = var.pfml_error_reports_path

        fineos_vendor_max_history_date  = var.fineos_vendor_max_history_date
        fineos_payment_max_history_date = var.fineos_payment_max_history_date

        dfml_project_manager_email_address = var.dfml_project_manager_email_address
      }
    },

    "pub-payments-process-fineos" = {
      command             = ["pub-payments-process-fineos"]
      containers_template = "pub_payments_process_fineos_template.json"
      task_role           = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-fineos"
      cpu                 = "2048"
      memory              = "16384"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        fineos_data_export_path = var.fineos_data_export_path
        fineos_data_import_path = var.fineos_data_import_path
      }
    },

    "fineos-test-vendor-export-generate" = {
      command             = ["fineos-test-vendor-export-generate"]
      task_role           = aws_iam_role.payments_fineos_process_task_role.arn
      containers_template = "fineos_test_vendor_export_generate.json"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id
      }
    },

    "fineos-bucket-tool" = {
      command             = ["fineos-bucket-tool"]
      containers_template = "fineos_bucket_tool.json"
      task_role           = aws_iam_role.fineos_bucket_tool_role.arn
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id
      }
    },

    "cps-errors" = {
      command             = ["cps-errors"]
      containers_template = "default_template.json"
      task_role           = aws_iam_role.cps_errors_task_role.arn
    },

    "payments-rotate-data-mart-password" = {
      command             = ["payments-rotate-data-mart-password"]
      containers_template = "payments_rotate_data_mart_password_template.json"
      task_role           = aws_iam_role.payments_ctr_process_task_role.arn
      vars = {
        ctr_data_mart_host     = var.ctr_data_mart_host
        ctr_data_mart_username = var.ctr_data_mart_username
      }
    },

    "payments-ctr-vc-code-cleanup" = {
      command             = ["payments-ctr-vc-code-cleanup"]
      containers_template = "payments_ctr_vc_code_cleanup_template.json"
      task_role           = aws_iam_role.payments_ctr_process_task_role.arn
      vars = {
        ctr_data_mart_host     = var.ctr_data_mart_host
        ctr_data_mart_username = var.ctr_data_mart_username
      }
    },

    "payments-payment-voucher-plus" = {
      command             = ["payments-payment-voucher-plus"]
      containers_template = "payments_payment_voucher_plus_template.json"
      task_role           = aws_iam_role.payments_fineos_process_task_role.arn
      cpu                 = "2048"
      memory              = "16384"
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        fineos_data_export_path  = var.fineos_data_export_path
        pfml_fineos_inbound_path = var.pfml_fineos_inbound_path
        pfml_error_reports_path  = var.pfml_error_reports_path
        pfml_voucher_output_path = var.pfml_voucher_output_path

        fineos_vendor_max_history_date = var.fineos_vendor_max_history_date

        pfml_email_address                     = var.pfml_email_address
        dfml_business_operations_email_address = var.dfml_business_operations_email_address

        ctr_data_mart_host     = var.ctr_data_mart_host
        ctr_data_mart_username = var.ctr_data_mart_username
      }
    },

    "transmogrify-state" = {
      command = ["transmogrify-state"]
    },

    "import-fineos-to-warehouse" = {
      command             = ["import-fineos-to-warehouse"]
      containers_template = "import_fineos_to_warehouse.json"
      task_role           = aws_iam_role.fineos_bucket_tool_role.arn
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id
        fineos_data_export_path         = var.fineos_data_export_path
      }
    },
  }
}

data "aws_ecr_repository" "app" {
  name = local.app_name
}

# this resource is used as a template to provision each ECS task in locals.tasks
resource "aws_ecs_task_definition" "ecs_tasks" {
  for_each                 = local.tasks
  family                   = "${local.app_name}-${var.environment_name}-${each.key}"
  task_role_arn            = lookup(each.value, "task_role", null)
  execution_role_arn       = lookup(each.value, "execution_role", aws_iam_role.task_executor.arn)
  container_definitions    = data.template_file.task_container_definitions[each.key].rendered
  cpu                      = lookup(each.value, "cpu", "512")
  memory                   = lookup(each.value, "memory", "1024")
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })
}

data "template_file" "task_container_definitions" {
  for_each = local.tasks
  template = file("${path.module}/json/${lookup(each.value, "containers_template", "default_template.json")}")

  vars = merge({
    app_name                   = local.app_name
    task_name                  = each.key
    command                    = jsonencode(each.value.command)
    cpu                        = lookup(each.value, "cpu", "512")
    memory                     = lookup(each.value, "memory", "1024")
    db_host                    = data.aws_db_instance.default.address
    db_name                    = data.aws_db_instance.default.db_name
    db_username                = data.aws_db_instance.default.master_username
    logging_level              = var.logging_level
    docker_image               = "${data.aws_ecr_repository.app.repository_url}:${var.service_docker_tag}"
    environment_name           = var.environment_name
    cloudwatch_logs_group_name = aws_cloudwatch_log_group.ecs_tasks.name
    aws_region                 = data.aws_region.current.name

    pfml_email_address                     = var.pfml_email_address
    bounce_forwarding_email_address        = var.bounce_forwarding_email_address
    bounce_forwarding_email_address_arn    = var.bounce_forwarding_email_address_arn
    ctr_gax_bievnt_email_address           = var.ctr_gax_bievnt_email_address
    ctr_vcc_bievnt_email_address           = var.ctr_vcc_bievnt_email_address
    dfml_business_operations_email_address = var.dfml_business_operations_email_address
  }, lookup(each.value, "vars", {}))
}
