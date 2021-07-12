# This file contains collections of environment variables that are required for various purposes in ECS tasks.
#
# Most things that are shared between multiple ECS tasks end up here to consolidate the code and ensure changes
# are made consistently across tasks without risk of missing one thing or another.
#
# Configuration that is _not_ shared across tasks can be provided inline in tasks.tf.
#
locals {
  # Configuration required for every ECS task
  common = [
    { name : "ENVIRONMENT", value : var.environment_name },
    { name : "LOGGING_LEVEL", value : var.logging_level },
    { name : "FEATURES_FILE_PATH", value : "s3://massgov-pfml-${var.environment_name}-feature-gate/features.yaml" },
    { name : "NEW_RELIC_LICENSE_KEY", valueFrom : "/service/${local.app_name}/common/newrelic-license-key" },
    { name : "NR_INSERT_API_KEY", valueFrom : "/admin/${local.app_name}/newrelic-insert-api-key" }
  ]

  # Provides access to the RDS database via admin username/password
  db_access = [
    { name : "DB_HOST", value : data.aws_db_instance.default.address },
    { name : "DB_NAME", value : data.aws_db_instance.default.db_name },
    { name : "DB_USERNAME", value : data.aws_db_instance.default.master_username },
    { name : "DB_PASSWORD", valueFrom : "/service/${local.app_name}/${var.environment_name}/db-password" }
  ]

  # Provides access to the FINEOS APIs
  fineos_api_access = [
    { name : "FINEOS_CLIENT_CUSTOMER_API_URL", value : var.fineos_client_customer_api_url },
    { name : "FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL", value : var.fineos_client_integration_services_api_url },
    { name : "FINEOS_CLIENT_GROUP_CLIENT_API_URL", value : var.fineos_client_group_client_api_url },
    { name : "FINEOS_CLIENT_WSCOMPOSER_API_URL", value : var.fineos_client_wscomposer_api_url },
    { name : "FINEOS_CLIENT_WSCOMPOSER_USER_ID", value : var.fineos_client_wscomposer_user_id },
    { name : "FINEOS_CLIENT_OAUTH2_URL", value : var.fineos_client_oauth2_url },
    { name : "FINEOS_CLIENT_OAUTH2_CLIENT_ID", value : var.fineos_client_oauth2_client_id },
    { name : "FINEOS_CLIENT_OAUTH2_CLIENT_SECRET", valueFrom : "/service/${local.app_name}/${var.environment_name}/fineos_oauth2_client_secret" }
  ]

  # Provides access to the FINEOS S3 buckets
  fineos_s3_access = [
    { name : "FINEOS_AWS_IAM_ROLE_ARN", value : var.fineos_aws_iam_role_arn },
    { name : "FINEOS_AWS_IAM_ROLE_EXTERNAL_ID", value : var.fineos_aws_iam_role_external_id },
    { name : "FINEOS_DATA_IMPORT_PATH", value : var.fineos_data_import_path },
    { name : "FINEOS_DATA_EXPORT_PATH", value : var.fineos_data_export_path },
    # This should just be fineos_data_export_path but we'll roll with this for now
    # to avoid breaking the camel's back
    { name : "FINEOS_FOLDER_PATH", value : var.fineos_import_employee_updates_input_directory_path }
  ]

  # Provides access to EOLWD's SFTP server (MoveIT)
  eolwd_moveit_access = [
    { name : "EOLWD_MOVEIT_SFTP_URI", value : var.eolwd_moveit_sftp_uri },
    { name : "CTR_MOVEIT_SSH_KEY", valueFrom : "/service/${local.app_name}-comptroller/${var.environment_name}/eolwd-moveit-ssh-key" },
    { name : "CTR_MOVEIT_SSH_KEY_PASSWORD", valueFrom : "/service/${local.app_name}-comptroller/${var.environment_name}/eolwd-moveit-ssh-key-password" },
    # Duplicate this for now since reductions has a different name
    { name : "MOVEIT_SFTP_URI", value : var.eolwd_moveit_sftp_uri },
    { name : "MOVEIT_SSH_KEY", valueFrom : "/service/${local.app_name}-comptroller/${var.environment_name}/eolwd-moveit-ssh-key" },
    { name : "MOVEIT_SSH_KEY_PASSWORD", valueFrom : "/service/${local.app_name}-comptroller/${var.environment_name}/eolwd-moveit-ssh-key-password" }
  ]

  # Provides access to CTR datamart
  datamart_access = [
    { name : "CTR_DATA_MART_HOST", value : var.ctr_data_mart_host },
    { name : "CTR_DATA_MART_USERNAME", value : var.ctr_data_mart_username },
    { name : "CTR_DATA_MART_PASSWORD", valueFrom : "/service/${local.app_name}/${var.environment_name}/ctr-data-mart-password" }
  ]

  # S3 path configurations for PUB
  pub_s3_folders = [
    { name : "PFML_FINEOS_WRITEBACK_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/cps/pei-writeback" },
    { name : "PFML_FINEOS_EXTRACT_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/cps/extracts" },
    { name : "DFML_REPORT_OUTBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-reports/dfml-reports" },
    { name : "DFML_RESPONSE_INBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-reports/dfml-responses" },
    { name : "PUB_MOVEIT_INBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/pub/inbound" },
    { name : "PUB_MOVEIT_OUTBOUND_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/pub/outbound" },
    { name : "PFML_ERROR_REPORTS_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/reports" },
    { name : "PFML_PAYMENT_REJECTS_ARCHIVE_PATH", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/audit" }
  ]

  # Moveit and S3 path configurations for reductions
  reductions_folders = [
    { name : "MOVEIT_DIA_INBOUND_PATH", value : "/DFML/DIA/Inbound" },
    { name : "MOVEIT_DUA_INBOUND_PATH", value : "/DFML/DUA/Outbound" },
    { name : "MOVEIT_DIA_OUTBOUND_PATH", value : "/DFML/DIA/Outbound" },
    { name : "MOVEIT_DUA_OUTBOUND_PATH", value : "/DFML/DUA/Inbound" },
    { name : "S3_BUCKET", value : "s3://massgov-pfml-${var.environment_name}-agency-transfer/" }

  ]

  # Basic configuration for sender email
  emails = [
    { name : "PFML_EMAIL_ADDRESS", value : var.pfml_email_address },
    { name : "BOUNCE_FORWARDING_EMAIL_ADDRESS", value : var.bounce_forwarding_email_address },
    { name : "BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", value : var.bounce_forwarding_email_address_arn }
  ]

  # Configuration for email sending + destinations required for payments
  emails_ctr = concat(local.emails, [
    { name : "CTR_GAX_BIEVNT_EMAIL_ADDRESS", value : var.ctr_gax_bievnt_email_address },
    { name : "CTR_VCC_BIEVNT_EMAIL_ADDRESS", value : var.ctr_vcc_bievnt_email_address },
    { name : "DFML_PROJECT_MANAGER_EMAIL_ADDRESS", value : var.dfml_project_manager_email_address },
    { name : "DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", value : var.dfml_business_operations_email_address },
  ])

  # Configuration for email sending + destinations required for reductions
  emails_reductions = concat(local.emails, [
    { name : "AGENCY_REDUCTIONS_EMAIL_ADDRESS", value : var.agency_reductions_email_address }
  ])
}
