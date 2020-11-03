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

variable "fineos_client_wscomposer_api_url" {
  description = "URL of the FINEOS Web Services Composer API"
  type        = string
  default     = ""
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
