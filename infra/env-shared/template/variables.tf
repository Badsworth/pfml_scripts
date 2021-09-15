variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "nlb_name" {
  description = "Name of the NLB"
  type        = string
}

variable "nlb_vpc_link_name" {
  description = "Name of the VPC Link between NLB and API Gateway"
  type        = string
}

variable "nlb_port" {
  description = "Port of the NLB that will map to the appropriate API"
  type        = string
}

variable "enable_regional_rate_based_acl" {
  description = "Test if current environment gets a rate-based acl on the API Gateway"
  type        = bool
  default     = false
}

variable "enable_fortinet_managed_rules" {
  description = "Test if current environment gets the Fortinet Managed Rules ACL on the API Gateway"
  type        = bool
  default     = false
}

variable "enforce_fortinet_managed_rules" {
  description = "Instructs Fortinet Managed Rules to either to block or count rule-matches"
  type        = bool
  default     = false
}
variable "runtime_py" {
  description = "Pointer to the Python runtime used by the PFML API lambdas"
  type        = string
  default     = "python3.9"
}

variable "is_adhoc_workspace" {
  description = "Whether this is running as a personal, adhoc workspace"
  type        = bool
  default     = false
}
