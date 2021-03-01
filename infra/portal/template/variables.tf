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

variable "cognito_enable_provisioned_concurrency" {
  description = "Enable or disable provisioned concurrency (and new-version publishing) for Cognito lambdas."
  type        = bool
  default     = false
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
  default     = "PFML_DoNotReply@eol.mass.gov"
}

variable "enforce_cloudfront_rate_limit" {
  type    = bool
  default = true
}

variable "enforce_cloudfront_fortinet_rules" {
  type    = bool
  default = true
}
