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

    "ad-hoc-verification" = {
      command = ["generate-verification-codes",
        "--input=s3://massgov-pfml-${var.environment_name}-verification-codes/source.csv",
      "--output=s3://massgov-pfml-${var.environment_name}-verification-codes/output.csv"],
      task_role = aws_iam_role.task_adhoc_verification_task_role.arn
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
      vars = {
        ctr_moveit_incoming_path = var.payments_ctr_moveit_incoming_path
        ctr_moveit_archive_path  = var.payments_ctr_moveit_archive_path
        pfml_ctr_inbound_path    = var.payments_pfml_ctr_inbound_path
        ctr_moveit_outgoing_path = var.payments_ctr_moveit_outgoing_path
        pfml_ctr_outbound_path   = var.payments_pfml_ctr_outbound_path

        payments_gax_bievnt_email               = var.payments_gax_bievnt_email
        pfml_email_address                      = var.pfml_email_address
        bounce_forwarding_email_address         = var.bounce_forwarding_email_address
        payments_dfml_business_operations_email = var.payments_dfml_business_operations_email

        ctr_data_mart_host     = var.ctr_data_mart_host
        ctr_data_mart_username = var.ctr_data_mart_username
      }
    },

    "payments-fineos-process" = {
      command             = ["payments-fineos-process"]
      containers_template = "payments_fineos_process_template.json"
      task_role           = aws_iam_role.payments_fineos_process_task_role.arn
      vars = {
        fineos_aws_iam_role_arn         = var.fineos_aws_iam_role_arn
        fineos_aws_iam_role_external_id = var.fineos_aws_iam_role_external_id

        fineos_data_export_path   = var.payments_fineos_data_export_path
        pfml_fineos_inbound_path  = var.payments_pfml_fineos_inbound_path
        fineos_data_import_path   = var.payments_fineos_data_import_path
        pfml_fineos_outbound_path = var.payments_pfml_fineos_outbound_path
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
  }, lookup(each.value, "vars", {}))
}
