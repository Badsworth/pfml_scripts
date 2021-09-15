variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "service_docker_tag" {
  description = "Tag of the docker image to associate with ECS tasks"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID."
  type        = string
}

variable "app_subnet_ids" {
  type        = list(string)
  description = "App subnet IDS."
  default     = []
}

variable "fineos_client_customer_api_url" {
  description = "URL of the FINEOS Customer API"
  type        = string
  default     = ""
}

variable "fineos_client_group_client_api_url" {
  description = "URL of the FINEOS Group Client API"
  type        = string
  default     = ""
}

variable "fineos_client_integration_services_api_url" {
  description = "URL of the FINEOS Integration Services API"
  type        = string
  default     = ""
}

variable "fineos_client_wscomposer_api_url" {
  description = "URL of the FINEOS Web Services Composer API"
  type        = string
  default     = ""
}

variable "fineos_client_wscomposer_user_id" {
  description = "User id for FINEOS Web Services Composer API"
  type        = string
  default     = "CONTENT"
}

variable "fineos_client_oauth2_url" {
  description = "URL of the FINEOS OAuth2 token endpoint."
  type        = string
  default     = ""
}

variable "fineos_client_oauth2_client_id" {
  description = "ID for the FINEOS OAuth2 client"
  type        = string
  default     = ""
}

variable "fineos_aws_iam_role_arn" {
  description = "ARN for role in the FINEOS AWS account that must be used to access resources inside of it"
  type        = string
  default     = ""
}

variable "fineos_aws_iam_role_external_id" {
  description = "ExternalId paramter for assuming role specified by fineos_aws_iam_role_arn"
  type        = string
  default     = ""
}

variable "fineos_report_export_path" {
  description = "Location for additional FINEOS exports"
  type        = string
  default     = ""
}
variable "fineos_eligibility_feed_output_directory_path" {
  description = "Location the FINEOS Eligibility Feed export should write output to"
  type        = string
  default     = ""
}

variable "fineos_import_employee_updates_input_directory_path" {
  description = "Location of the FINEOS extract to process into our DB."
  type        = string
  default     = null
}

variable "logging_level" {
  description = "Logging level override"
  type        = string
  default     = ""
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
  default     = ""
}

variable "fineos_data_export_path" {
  description = "FINEOS generates data export files for PFML API to pick up"
  type        = string
  default     = ""
}

variable "fineos_data_import_path" {
  description = "PFML API generates files for FINEOS to process"
  type        = string
  default     = ""
}

variable "fineos_error_export_path" {
  description = "FINEOS generates error export files for PFML API to pick up"
  type        = string
  default     = ""
}

variable "pfml_fineos_inbound_path" {
  description = "PFML API stores a copy of all files that FINEOS generates for us"
  type        = string
  default     = ""
}

variable "pfml_fineos_outbound_path" {
  description = "PFML API stores a copy of all files that we generate for FINEOS"
  type        = string
  default     = ""
}

variable "dor_fineos_etl_schedule_expression" {
  # Daily at 04:30 UTC [12:30 EST] [13:30 EDT]
  description = "EventBridge schedule for DOR FINEOS ETL"
  type        = string
  default     = "cron(30 4 * * ? *)"
}

variable "eolwd_moveit_sftp_uri" {
  description = "URI for LWD MOVEit instance"
  type        = string
  default     = ""
}

variable "pfml_error_reports_path" {
  description = "PFML API stores a copy of all error reports generated"
  type        = string
  default     = ""
}

variable "pfml_email_address" {
  description = "Generic send from address for outgoing emails"
  type        = string
  default     = ""
}

variable "dfml_project_manager_email_address" {
  description = "DFML Project manager email address"
  type        = string
  default     = ""
}

variable "bounce_forwarding_email_address" {
  description = "Generic send to address for bounced back outgoing email notifications"
  type        = string
  default     = ""
}

variable "bounce_forwarding_email_address_arn" {
  description = "Generic send to address for bounced back outgoing email notifications (ARN)"
  type        = string
  default     = ""
}

variable "dfml_business_operations_email_address" {
  description = "Email address for DFML Business Operations team"
  type        = string
  default     = ""
}

variable "agency_reductions_email_address" {
  description = "Generic send from address for outgoing emails"
  type        = string
  default     = ""
}

variable "enable_register_admins_job" {
  description = "Is the cloudwatch event to register admins enabled?"
  type        = bool
  default     = true
}

variable "task_failure_email_address_list" {
  type        = list(string)
  description = "List of email addresses"
  default     = []
}

variable "enable_reductions_send_claimant_lists_to_agencies_schedule" {
  description = "Enable scheduling for 'reductions-send-claimant-lists-to-agencies' ECS task"
  type        = bool
  default     = false
}

variable "enable_reductions_process_agency_data_schedule" {
  description = "Enable scheduling for 'reductions-process-agency-data' ECS task"
  type        = bool
  default     = false
}

variable "payment_audit_report_outbound_folder_path" {
  description = "Payment audit report outbound folder path"
  type        = string
  default     = ""
}

variable "payment_audit_report_sent_folder_path" {
  description = "Payment audit report sent folder path"
  type        = string
  default     = ""
}

variable "enable_pub_automation_fineos" {
  description = "Enable scheduling for pub automation fineos task"
  default     = false
}

variable "enable_pub_automation_create_pub_files" {
  description = "Enable scheduling for pub automation create pub files task"
  default     = false
}

variable "enable_pub_automation_process_returns" {
  description = "Enable scheduling for pub automation return processing task"
  default     = false
}

variable "rmv_client_base_url" {
  description = "The base URL for the Registry of Motor Vehicles (RMV) API."
  type        = string
  default     = ""
}

variable "rmv_client_certificate_binary_arn" {
  description = "The secretsmanager ARN for the Registry of Motor Vehicles (RMV) certificate."
  type        = string
  default     = ""
}

variable "rmv_api_behavior" {
  description = "Specifies if the RMV response is mocked"
  type        = string
  default     = "fully_mocked"
}

########## Variables for Step Functions ################

variable "st_use_mock_dor_data" {
  description = "Step Function Mock DOR Data"
  default     = false
}

variable "st_decrypt_dor_data" {
  description = "Step Function Decrypted DOR Data"
  default     = false
}

variable "st_file_limit_specified" {
  description = "Step Function Eligibility Feed Export File Number Limit"
  default     = true
}

variable "st_employer_update_limit" {
  description = "Employer Upload Update Limit"
  type        = number
}