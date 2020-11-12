variable "cloudfront_origin_path" {
  description = "Path to latest portal release. Set through environment variable in Github worfklow."
  type        = string
}

variable "cognito_extra_redirect_urls" {
  description = "Additional list of valid URLs for Cognito to redirect to after user authentication"
  type        = list(string)
  default     = []
}

variable "cognito_extra_logout_urls" {
  description = "Additional list of valid URLs for Cognito to redirect to after logout"
  type        = list(string)
  default     = []
}

variable "domain" {
  description = "Domain name to point to CloudFront distribution (including TLD)"
  type        = string
  default     = ""
}

variable "environment_name" {
  description = "Name of the environment (dev, sandbox, test, uat, stage, prod)"
  type        = string
}

variable "ses_email_address" {
  description = "Email address used to send Cognito emails. Note that in order to use it at production scale or to send to out-of-domain email addresses we'll need to manually request that the SES email be removed from the SES sandbox"
  type        = string
  default     = "noreplypfml@mass.gov"
}

variable "cognito_post_confirmation_lambda_arn" {
  description = "Optional. ARN of AWS Lambda to connect to the post-confirmation event on the Cognito User Pool."
  type        = string
  default     = null
}

variable "cognito_pre_signup_lambda_arn" {
  description = "Optional. ARN of AWS Lambda to connect to the pre-signup event on the Cognito User Pool."
  type        = string
  default     = null
}
