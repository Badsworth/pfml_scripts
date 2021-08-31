# Templating and configurations for ECS tasks.
#
# If you need to add a new ECS task, add it to the locals.tasks variable
# in the following format:
#
# "${local.app_name}-your-task-name" = {
#   command = ["the-command-name"],
#   env = [
#     local.db_access,
#     ...
#   ]
# }
#
# The command name comes from pyproject.toml.
#
# Application AWS Permissions
# ===========================
#
# The task_role should be defined, but can be null if your running task does not need
# to be assigned an IAM role for additional permissions to AWS resources.
# If not null, it should have a task_role_arn stored in it for the aws_ecs_task_definition.
#
# Configuring Environment Variables and Secrets
# =============================================
#
# If your task requires unique SSM / secretsmanager permissions, please define and specify an
# execution_role for your task.
#
# Use the "env" key to specify the environment variables needed by your ECS task. Shared groups of variables
# are stored as locals in task_config.tf and can be used:
#
# env = [ local.db_access ]
#
# If you need unique variables, you can specify them inline:
#
# env = [
#   local.db_access,
#   { name: "COOL_ENDPOINT_URL", value: "something" }
# ]
#
# You can also specify secrets that are pulled from parameter store using the "valueFrom" key:
#
# env = [
#   local.db_access,
#   { name: "COOL_ENDPOINT_URL", value: "something" },
#   { name: "COOL_ENDPOINT_SECRET_KEY", valueFrom: "/service/pfml-api/test/cool_endpoint_secret_key" }
# ]
#
# Note that AWS ECS provides protections against duplicate or invalid keys. This won't be caught at the PR stage,
# but a terraform apply will indicate any AWS errors, e.g.:
#
# Error: ClientException: Duplicate secret names found: DB_NESSUS_PASSWORD. Each secret name must be unique.
#
# Resource Limits
# ===============
#
# CPU and memory defaults are 1024 (CPU units) and 2048 (MB).
# 1/4th of that allocation (256 CPU units, 512MB RAM) is reserved for the New Relic infra sidecar.
# This leaves the default resource allocation available to your business logic as: 768 CPU units, 1.5GB RAM.

# If you need more resources than this, add "cpu" or "memory" keys to your ECS task's
# entry in locals.tasks. The defaults will be used if these keys are absent.
#
# Testing ECS Tasks
# =================
#
# Once you're ready, apply your terraform changes and test your new ECS task in the test environment.
#
# From the root of the git repository (example):
#
# ./bin/run-ecs-task/run-task.sh test db-migrate-up kevin.yeh
#
locals {
  tasks = {
    "db-migrate-up" = {
      command = ["db-migrate-up"],
      env     = [local.db_access]
    },

    "db-migrate-down" = {
      command = ["db-migrate-down"]
      env     = [local.db_access]
    }

    "db-admin-create-db-users" = {
      command = ["db-admin-create-db-users"]
      env = [
        local.db_access,
        { name : "DB_NESSUS_PASSWORD", valueFrom : "/service/${local.app_name}/${var.environment_name}/db-nessus-password" }
      ]
    },

    "db-create-fineos-user" = {
      command = ["db-create-fineos-user"],
      env = [
        local.db_access,
        { name : "COGNITO_FINEOS_APP_CLIENT_ID", valueFrom : "/service/${local.app_name}/${var.environment_name}/cognito_fineos_app_client_id" },
        { name : "COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", valueFrom : "/service/${local.app_name}/${var.environment_name}/cognito_internal_fineos_role_app_client_id" }
      ]
    },

    "execute-sql" = {
      command   = ["execute-sql"]
      task_role = aws_iam_role.task_execute_sql_task_role.arn
      env = [
        local.db_access,
        { name : "S3_EXPORT_BUCKET", value : "massgov-pfml-${var.environment_name}-execute-sql-export" }
      ]
    },

    "dor-import" = {
      command        = ["dor-import"],
      task_role      = aws_iam_role.dor_import_task_role.arn,
      execution_role = aws_iam_role.dor_import_execution_role.arn,
      cpu            = 4096,
      memory         = 18432,
      env = [
        local.db_access,
        { name : "DECRYPT", value : "true" },
        { name : "FOLDER_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/dor/received" },
        { name : "GPG_DECRYPTION_KEY", valueFrom : "/service/${local.app_name}-dor-import/${var.environment_name}/gpg_decryption_key" },
        { name : "GPG_DECRYPTION_KEY_PASSPHRASE", valueFrom : "/service/${local.app_name}-dor-import/${var.environment_name}/gpg_decryption_key_passphrase" }
      ]
    },

    "fineos-import-employee-updates" = {
      command   = ["fineos-import-employee-updates"]
      task_role = aws_iam_role.fineos_import_employee_updates_task_role.arn
      cpu       = 2048
      memory    = 9216
      env = [
        local.db_access,
        local.fineos_s3_access
      ]
    },

    "register-leave-admins-with-fineos" = {
      command   = ["register-leave-admins-with-fineos"]
      task_role = aws_iam_role.register_admins_task_role.arn,
      cpu       = 4096,
      memory    = 18432,
      env = [
        local.db_access,
        local.fineos_api_access
      ]
    }

    "load-employers-to-fineos" = {
      command = ["load-employers-to-fineos"]
      env = [
        local.db_access,
        local.fineos_api_access
      ]
    },

    "reductions-process-agency-data" = {
      command        = ["reductions-process-agency-data"]
      task_role      = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow"
      execution_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-wrkflw-execution-role"
      env = [
        local.db_access,
        local.eolwd_moveit_access,
        local.reductions_folders,
        local.emails_reductions
      ]
    },

    "reductions-send-claimant-lists" = {
      command        = ["reductions-send-claimant-lists-to-agencies"]
      task_role      = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow"
      execution_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-reductions-wrkflw-execution-role"
      env = [
        local.db_access,
        local.eolwd_moveit_access,
        local.reductions_folders
      ]
    },

    "pub-payments-create-pub-files" = {
      command   = ["pub-payments-create-pub-files"]
      task_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-pub-payments-create-pub-files"
      env = [
        local.db_access,
        local.fineos_s3_access,
        local.pub_s3_folders,
        { name : "PUB_PAYMENT_STARTING_CHECK_NUMBER", value : "106" },
        { name : "DFML_PUB_ROUTING_NUMBER", valueFrom : "/service/${local.app_name}/${var.environment_name}/dfml_pub_routing_number" },
        { name : "DFML_PUB_ACCOUNT_NUMBER", valueFrom : "/service/${local.app_name}/${var.environment_name}/dfml_pub_account_number" }
      ]
    },

    "pub-payments-process-pub-returns" = {
      command   = ["pub-payments-process-pub-returns"]
      task_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-pub-payments-process-pub-returns"
      env = [
        local.db_access,
        local.fineos_s3_access,
        local.pub_s3_folders
      ]
    },

    "fineos-eligibility-feed-export" = {
      command   = ["fineos-eligibility-feed-export"]
      task_role = aws_iam_role.fineos_eligibility_feed_export_task_role.arn
      cpu       = 4096
      memory    = 8192
      env = [
        local.db_access,
        local.fineos_api_access,
        local.fineos_s3_access,
        { "name" : "OUTPUT_DIRECTORY_PATH", "value" : "${var.fineos_eligibility_feed_output_directory_path}" }
      ]
    }

    "pub-payments-process-fineos" = {
      command   = ["pub-payments-process-fineos"]
      task_role = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-fineos"
      cpu       = 2048
      memory    = 16384
      env = [
        local.db_access,
        local.fineos_s3_access,
        local.pub_s3_folders,
        { name : "FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", value : "2021-06-12" },
        { name : "FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", value : "2021-06-12" },
        { name : "USE_EXPERIAN_SOAP_CLIENT", value : "1" },
        { name : "EXPERIAN_AUTH_TOKEN", valueFrom : "/service/${local.app_name}/common/experian-auth-token" }
      ]
    },

    "fineos-bucket-tool" = {
      command   = ["fineos-bucket-tool"]
      task_role = aws_iam_role.fineos_bucket_tool_role.arn
      env = [
        local.fineos_s3_access
      ]
    },

    "cps-errors-crawler" = {
      command             = ["cps-errors-crawler"]
      containers_template = "default_template.json"
      task_role           = aws_iam_role.cps_errors_crawler_task_role.arn
      env = [
        { name : "CPS_ERROR_REPORTS_RECEIVED_S3_PATH", value : "s3://${data.aws_s3_bucket.agency_transfer.id}/cps-errors/received/" },
        { name : "CPS_ERROR_REPORTS_PROCESSED_S3_PATH", value : "s3://${data.aws_s3_bucket.agency_transfer.id}/cps-errors/processed/" },
      ]

    },

    "import-fineos-to-warehouse" = {
      command   = ["import-fineos-to-warehouse"]
      task_role = aws_iam_role.fineos_bucket_tool_role.arn
      env = [
        local.fineos_s3_access,
        { name : "BI_WAREHOUSE_PATH", value : "s3://massgov-pfml-${var.environment_name}-business-intelligence-tool/warehouse/raw/fineos/" }
      ]
    },

    "update-gender-data-from-rmv" = {
      command   = ["update-gender-data-from-rmv"]
      task_role = aws_iam_role.update_gender_data_from_rmv_task_role.arn
      env = [
        local.db_access,
        local.rmv_api_access
      ]
    },
  }
}

data "aws_ecr_repository" "app" {
  name = local.app_name
}

# this resource is used as a template to provision each ECS task in local.tasks
resource "aws_ecs_task_definition" "ecs_tasks" {
  for_each                 = local.tasks
  family                   = "${local.app_name}-${var.environment_name}-${each.key}"
  task_role_arn            = lookup(each.value, "task_role", null)
  execution_role_arn       = lookup(each.value, "execution_role", aws_iam_role.task_executor.arn)
  cpu                      = tostring(lookup(each.value, "cpu", 1024))
  memory                   = tostring(lookup(each.value, "memory", 2048))
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })

  container_definitions = jsonencode([
    {
      name                   = each.key,
      image                  = format("%s:%s", data.aws_ecr_repository.app.repository_url, var.service_docker_tag),
      command                = each.value.command,
      cpu                    = tonumber(lookup(each.value, "cpu", 1024)) - 256,
      memory                 = tonumber(lookup(each.value, "memory", 2048)) - 512,
      networkMode            = "awsvpc",
      essential              = true,
      readonlyRootFilesystem = false, # False by default; some tasks write local files.
      linuxParameters = {
        capabilities = {
          drop = ["ALL"]
        },
        initProcessEnabled = true
      },
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_tasks.name,
          "awslogs-region"        = data.aws_region.current.name,
          "awslogs-stream-prefix" = var.environment_name
        }
      },

      # Split env into static environment variables or secrets based on whether they contain "value" or "valueFrom"
      # I know, it's not very readable but this is how terraform is.
      #
      # We use !contains("value") for secrets instead of contains("valueFrom") so that any items with typos are
      # caught and error out when trying to apply the task definition. Otherwise, anything with a typo could
      # silently cause env vars to go missing which would definitely confuse someone for a day or two.
      #
      environment = [for val in flatten(concat(lookup(each.value, "env", []), local.common)) : val if contains(keys(val), "value")]
      secrets     = [for val in flatten(concat(lookup(each.value, "env", []), local.common)) : val if !contains(keys(val), "value")]
    },
    ###### ↑ Generic "business logic" container definition ↑ | ↓ New Relic infrastructure sidecar definition ↓ ######
    {
      name              = "newrelic-infra",
      image             = "498823821309.dkr.ecr.us-east-1.amazonaws.com/eolwd-pfml-dockerhub-mirror:newrelic.infrastructure-bundle.2.6.1",
      cpu               = 256,
      memoryReservation = 512,
      essential         = false,
      environment = [
        {
          name  = "NRIA_OVERRIDE_HOST_ROOT",
          value = ""
        },
        {
          name  = "NRIA_IS_FORWARD_ONLY",
          value = "true"
        },
        {
          name  = "FARGATE",
          value = "true"
        },
        {
          name  = "ENABLE_NRI_ECS",
          value = "true"
        },
        {
          name  = "NRIA_PASSTHROUGH_ENVIRONMENT",
          value = "ECS_CONTAINER_METADATA_URI,ENABLE_NRI_ECS,FARGATE"
        },
        {
          name  = "NRIA_CUSTOM_ATTRIBUTES",
          value = "{\"nrDeployMethod\":\"downloadPage\"}"
        }
      ],
      secrets = [
        {
          valueFrom : "/service/${local.app_name}/common/newrelic-license-key",
          name : "NRIA_LICENSE_KEY"
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_tasks.name,
          "awslogs-region"        = data.aws_region.current.name,
          "awslogs-stream-prefix" = var.environment_name
        }
      }
    }
  ])
}
