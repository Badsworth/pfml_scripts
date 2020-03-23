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

variable "cognito_use_ses_email" {
  description = "Whether Cognito should use an SES email sender (true) or the default Cognito email sender which includes various throttles (false)"
  type = bool
}

variable "cognito_sender_email" {
  description = "Email address used to send Cognito emails. Note that in order to use it at production scale or to send to out-of-domain email addresses we'll need to manually request that the SES email be removed from the SES sandbox"
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

variable "tld" {
  description = "Top-level domain name (primarily for finding ACM cert and Route53 hosted zone)"
  type        = string
  default     = "navateam.com"
}

variable "domain" {
  description = "Domain name to point to CloudFront distribution (including TLD), defaults to pfml-$(env_name).$(tld)"
  type        = string
  default     = ""
}

variable "cloudfront_origin_path" {
  description = "Path to latest portal release. Set through environment variable in Github worfklow."
  type        = string
}
