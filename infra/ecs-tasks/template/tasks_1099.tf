# Templating and configurations for ECS tasks with multiple containers
# NOTE: Pushed for collaboration. NOT READY TO MERGE

# this resource is used as a template to provision each ECS task in local.tasks
resource "aws_ecs_task_definition" "ecs_tasks_1099" {
  family                   = "${local.app_name}-${var.environment_name}-1099-form-generator"
  task_role_arn            = "arn:aws:iam::498823821309:role/${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099"
  execution_role_arn       = aws_iam_role.task_executor.arn
  cpu                      = tostring(4096)
  memory                   = tostring(8192)
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
  })



  //
  // This json needs to be dynamically created with each iteration
  // See task.tf
  //
  container_definitions = jsonencode([
    {
      name                   = "pub-payments-process-1099-documents",
      image                  = format("%s:%s", data.aws_ecr_repository.app.repository_url, var.service_docker_tag),
      command                = ["pub-payments-process-1099-documents"],
      cpu                    = 2048,
      memory                 = 4096,
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

      environment = [
        {
          name  = "DB_HOST"
          value = "massgov-pfml-test.c6icrkacncoz.us-east-1.rds.amazonaws.com"
        },
        {
          name  = "DB_HOST_TEST"
          value = "TEST"
        },
        {
          name  = "DB_NAME"
          value = "massgov_pfml_test"
        },
        { name : "FINEOS_AWS_IAM_ROLE_ARN", value : var.fineos_aws_iam_role_arn },
        { name : "FINEOS_AWS_IAM_ROLE_EXTERNAL_ID", value : var.fineos_aws_iam_role_external_id },
        { name : "FINEOS_DATA_IMPORT_PATH", value : var.fineos_data_import_path },
        { name : "FINEOS_DATA_EXPORT_PATH", value : var.fineos_data_export_path },
        { name : "FINEOS_ADHOC_DATA_EXPORT_PATH", value : var.fineos_adhoc_data_export_path },
        { name : "FINEOS_FOLDER_PATH", value : var.fineos_import_employee_updates_input_directory_path },
        { name : "PFML_FINEOS_WRITEBACK_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/cps/pei-writeback" },
        { name : "PFML_FINEOS_EXTRACT_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/cps/extracts" },
        { name : "DFML_REPORT_OUTBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-reports/dfml-reports" },
        { name : "DFML_RESPONSE_INBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-reports/dfml-responses" },
        { name : "PUB_MOVEIT_INBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/pub/inbound" },
        { name : "PUB_MOVEIT_OUTBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/pub/outbound" },
        { name : "PFML_PUB_ACH_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/pub/ach" },
        { name : "PFML_PUB_CHECK_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/pub/check" },
        { name : "PFML_ERROR_REPORTS_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/reports" },
        { name : "PFML_PAYMENT_REJECTS_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/audit" }
      ]
      secrets = [{
        name      = "DB_PASSWORD"
        valueFrom = "/service/pfml-api/test/db-password"
        },
        {
          name      = "RMV_CLIENT_CERTIFICATE_PASSWORD"
          valueFrom = "/service/pfml-api/test/rmv_client_certificate_password"
      }]
    },
    {
      name                   = "pub-payments-process-1099-dot-net-generator-service",
      image                  = "498823821309.dkr.ecr.us-east-1.amazonaws.com/pfml-api-dot-net-1099:latest",
      command                = ["dotnet", "PfmlPdfApi.dll"],
      cpu                    = 2048,
      memory                 = 4096,
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

      environment = []
      secrets     = []
    }
  ])
}
