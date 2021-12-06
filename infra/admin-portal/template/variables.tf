variable "cloudfront_origin_path" {
  description = "Path to latest portal release. Set through environment variable in Github worfklow."
  type        = string
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

variable "enforce_cloudfront_rate_limit" {
  type    = bool
  default = true
}

variable "enforce_cloudfront_fortinet_rules" {
  type    = bool
  default = true
}
