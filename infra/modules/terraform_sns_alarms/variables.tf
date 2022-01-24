variable "sns_monthly_spend_limit" {
  description = "SNS Monthly Spend Limit"
  type        = number
  default     = 1000.0
}

variable "low_priority_nr_integration_key" {
  description = "Low Priority NR Integration Key"
  type        = string
  default     = "low_priority_nr_integration_key"
}

variable "high_priority_nr_integration_key" {
  description = "High Priority NR Integration Key"
  type        = string
  default     = "high_priority_nr_integration_key"
}

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}