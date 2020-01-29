variable "cognito_redirect_url" {
  description = "URL for Cognito to redirect to after user authentication"
  type        = string
}

variable "cognito_logout_url" {
  description = "URL for Cognito to redirect to after logout"
  type        = string
}

variable "env_name" {
  description = "Name of the environment"
  type        = string
}

variable "portal_s3_bucket_name" {
  description = "Name of the deploy bucket for Claimant Portal"
  type        = string
}
