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
