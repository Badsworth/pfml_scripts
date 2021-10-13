variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "service_app_count" {
  description = "Number of application containers to run"
  type        = number
}

variable "service_max_app_count" {
  description = "Maximum number of application containers to run (under auto scaling)."
  type        = number
}

variable "service_docker_tag" {
  description = "Tag of the docker image to run"
  type        = string
}

variable "service_ecs_cluster_arn" {
  description = "ARN of the ECS cluster used to schedule app containers."
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID."
  type        = string
}

variable "vpc_app_subnet_ids" {
  description = "A list of app-level subnets within the VPC."
  type        = list(string)
}

variable "vpc_db_subnet_ids" {
  description = "A list of db-level subnets within the VPC."
  type        = list(string)
}

variable "postgres_version" {
  description = "The version of the postgres database."
  type        = string
  default     = "11.6"
}

variable "postgres_parameter_group_family" {
  description = "The parameter group family for the postgres database."
  type        = string
  default     = "postgres11"
}

variable "db_allocated_storage" {
  description = "The allocated storage in gibibytes."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "The upper limit for automatically scaled storage in gibibytes."
  type        = number
  default     = 100
}

variable "db_instance_class" {
  description = "The instance class of the database (RDS)."
  type        = string
  default     = "db.t3.small" # For now, this must be changed in AWS Console. Modifications to this field will yield no result.
}

variable "db_iops" {
  description = "The amount of provisioned IOPS."
  type        = number
  default     = null
}

variable "db_storage_type" {
  description = "Storage type, one of gp2 or io1."
  type        = string
  default     = "gp2" # For now, this must be changed in AWS Console. Modifications to this field will yield no result.
}

variable "db_multi_az" {
  description = "Specifies if the RDS instance is multi-AZ."
  type        = bool
  default     = false
}

variable "nlb_name" {
  description = "Name of the network load balancer to route from."
  type        = string
}

variable "nlb_port" {
  description = "Port of the network load balancer that has been reserved within the API Gateway."
  type        = string
}

variable "enable_full_error_logs" {
  description = "Enable logging of full request and response on errors"
  type        = string
  default     = "0"
}

variable "enable_alarm_api_cpu" {
  description = "Enable Cloudwatch alarms for API CPU Usage"
  type        = bool
  default     = true
}

variable "enable_alarm_api_ram" {
  description = "Enable Cloudwatch alarms for API RAM Usage"
  type        = bool
  default     = true
}


variable "cors_origins" {
  description = "A list of origins to allow CORS requests from."
  type        = list(string)
}

variable "runtime_py" {
  description = "Pointer to the Python runtime used by the PFML API lambdas"
  type        = string
  default     = "python3.9"
}

variable "cognito_user_pool_arn" {
  description = "The ARN of the Cognito User Pool."
  type        = string
  default     = null
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_user_pool_client_id" {
  type = string
}

variable "cognito_user_pool_keys_url" {
  description = "The URL to fetch the Cognito User Pool's JSON Web Key Set from."
  type        = string
  default     = null
}

variable "logging_level" {
  description = "Override default logging levels for certain Python modules."
  type        = string
  default     = ""
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

variable "rmv_check_mock_success" {
  description = "Specifies if RMV check mock response always passes. '1' always passes id proofing, '0' always fails id proofing."
  type        = string
  default     = "1"
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

variable "fineos_eligibility_feed_output_directory_path" {
  description = "Location the Eligibility Feed Lambda should write output to"
  type        = string
  default     = null
}

variable "fineos_import_employee_updates_input_directory_path" {
  description = "Location of the FINEOS extract to process into our DB."
  type        = string
  default     = null
}

variable "fineos_aws_iam_role_arn" {
  description = "ARN for role in the FINEOS AWS account that must be used to access resources inside of it"
  type        = string
  default     = null
}

variable "fineos_aws_iam_role_external_id" {
  description = "ExternalId paramter for assuming role specified by fineos_aws_iam_role_arn"
  type        = string
  default     = null
}

variable "service_now_base_url" {
  description = "URL for Service Now post requests"
  type        = string
  default     = ""
}

variable "portal_base_url" {
  description = "Portal base URL to use when creating links"
  type        = string
  default     = ""
}

variable "admin_portal_base_url" {
  description = "Admin Portal base URL to use when creating links"
  type        = string
  default     = ""
}

variable "enable_application_fraud_check" {
  description = "Enable the fraud check for application submission"
  type        = string
}

variable "cognito_enable_provisioned_concurrency" {
  description = "Enable or disable provisioned concurrency (and new-version publishing) for Cognito lambdas."
  type        = bool
  default     = false
}

variable "cognito_provisioned_concurrency_level_max" {
  description = "The number of Cognito lambdas that will be kept 'hot' during the working week."
  type        = number
  default     = 5
}

variable "cognito_provisioned_concurrency_level_min" {
  description = "The number of Cognito lambdas that will be kept 'hot' on nights and weekends."
  type        = number
  default     = 1
}

variable "release_version" {
  description = "API release version"
  type        = string
  default     = ""
}

variable "new_plan_proofs_active_at" {
  description = "ISO 8601 formatted date string, should explicitly set UTC offset (+00:00)"
  type        = string
  default     = "2021-06-21 00:00:00+00:00"
}

variable "use_claim_status_url" {
  description = "Whether or not to direct claimants to the claim status page. Can enable this when Claim Status is launched."
  type        = bool
  default     = false
}
