variable "sns_monthly_spend_limit" {
  description = "SNS Monthly Spend Limit"
  type        = number
  default     = 1000.0
}

variable "low_priority_nr_integration_key" {
  description = "Low Priority NewRelic Integration Key"
  type        = string
  default     = "low_priority_nr_integration_key"
}

variable "high_priority_nr_integration_key" {
  description = "High Priority NewRelic Integration Key"
  type        = string
  default     = "high_priority_nr_integration_key"
}

variable "low_priority_pager_duty_integration_key" {
  description = "Low Priority PagerDuty Integration Key"
  type        = string
  default     = "low_priority_pager_duty_integration_key"
}

variable "high_priority_pager_duty_integration_key" {
  description = "High Priority PagerDuty Integration Key"
  type        = string
  default     = "high_priority_pager_duty_integration_key"
}

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "sns_spending_thresholds" {
  description = "SNS Spending Limits Thresholds"
  type        = map(any)
  default = {
    information = 0.5,
    warning     = 0.8,
    critical    = 0.9,
    exceeded    = 1.0
  }
}

variable "sns_sms_failure_rate" {
  description = "SNS SMS Failure Rate"
  type        = map(any)
  default = {
    warning  = 0.4,
    critical = 0.25
  }
}

variable "carrier_unavailable_period" {
  description = "Period When SMS Phone Carrier Is Unavailable"
  type        = map(any)
  default = {
    warning  = 3600,
    critical = 7200
  }
}