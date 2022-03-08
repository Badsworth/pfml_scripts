###  metric alarm variables

variable "alarm_name" {
  description = "Name of metric alarm"
  type        = string
}

variable "alarm_description" {
  description = "Description of metric alarm"
  type        = string
}

variable "metric_name" {
  description = "Name of the metric"
  type        = string
}

### metric filter variables

variable "pattern" {
  description = "pattern of the metric filter"
  type        = string
}

variable "sns_topic" {
  description = "aws resource change sns topic"
  type        = string
}

variable "comparison_operator" {
  description = "cloudwatch metric alarm comparison_operator"
  type        = string
  default     = "GreaterThanOrEqualToThreshold"
}

variable "evaluation_periods" {
  description = "cloudwatch metric alarm evaluation_periods"
  type        = string
  default     = "1"
}

variable "namespace" {
  description = "namespace of cloudwatch metric filter and alarm"
  type        = string
}

variable "periods" {
  description = "periods of cloudwatch metric alarm"
  type        = string
  default     = "300"
}

variable "statistic" {
  description = "statistic of cloudwatch metric alarm"
  type        = string
  default     = "Sum"
}

variable "threshold" {
  description = "threshold of cloudwatch metric alarm"
  type        = string
  default     = "1"
}
