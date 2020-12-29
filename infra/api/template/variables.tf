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

variable "cors_origins" {
  description = "A list of origins to allow CORS requests from."
  type        = list(string)
}

variable "formstack_import_lambda_build_s3_key" {
  description = "The S3 object key of the Formstack integration lambda artifact"
  type        = string
}

variable "runtime_py" {
  description = "Pointer to the Python runtime used by the PFML API lambdas"
  type        = string
  default     = "python3.8"
}

variable "cognito_user_pool_arn" {
  description = "The ARN of the Cognito User Pool."
  type        = string
  default     = null
}

variable "cognito_post_confirmation_lambda_artifact_s3_key" {
  description = "The S3 object key of the Cognito Post Confirmation hook Lambda artifact"
  type        = string
}

variable "cognito_pre_signup_lambda_artifact_s3_key" {
  description = "The S3 object key of the Cognito Pre Signup hook Lambda artifact"
  type        = string
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

variable "rmv_check_behavior" {
  description = "Specifies if the RMV response is mocked"
  type        = string
  default     = "fully_mocked"
}

variable "rmv_check_mock_success" {
  description = "Specifies if RMV mock response always passes. '1' always passes id proofing, '0' always fails id proofing."
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

variable "fineos_eligibility_transfer_lambda_build_s3_key" {
  description = "The S3 object key of the FINEOS eligibility transfer lambda artifact"
  type        = string
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

variable "enable_application_fraud_check" {
  description = "Enable the fraud check for application submission"
  type        = string
}

variable "dor_fineos_etl_definition" {
  description = "Step function definition for DOR FINEOS ETL"
  type        = string
  default     = <<-END
    {
      "StartAt": "nothing",
      "States": {"nothing": {"Type": "Pass", "End": true}}
    }
    END
}

variable "dor_fineos_etl_schedule_expression" {
  description = "EventBridge schedule for DOR FINEOS ETL"
  type        = string
  default     = "cron(30 4 * * ? *)"
}

variable "cognito_enable_provisioned_concurrency" {
  description = "Enable or disable provisioned concurrency (and new-version publishing) for Cognito lambdas."
  type        = bool
  default     = false
}
