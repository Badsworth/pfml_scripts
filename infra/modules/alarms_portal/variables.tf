# variable for different environments 

variable "environment_name" {
  description = "Name of the environment (dev, sandbox, test, uat, stage, prod, breakfix, cps-preview)"
  type        = string
}

variable "low_priority_nr_portal_integration_key" {
  description = "Name of the integration key for Portal"
  type        = string
}

variable "high_priority_nr_portal_integration_key" {
  description = "Name of the integration key for Portal"
  type        = string
}