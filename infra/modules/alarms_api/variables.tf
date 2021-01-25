# variable for different environments

variable "environment_name" {
  description = "Name of the environment (dev, sandbox, test, uat, stage, prod)"
  type        = string
}

variable "low_priority_nr_integration_key" {
  description = "Name of the integration key"
  type        = string
}

variable "high_priority_nr_integration_key" {
  description = "Name of the integration key"
  type        = string
}

variable "warning_alert_sns_topic_arn" {
  description = "SNS topic ARN for cloudwatch warning alarms"
  type        = string
}

variable "critical_alert_sns_topic_arn" {
  description = "SNS topic ARN for cloudwatch critical alarms"
  type        = string
}

variable "enable_alarm_api_cpu" {
  description = "CPU Alarm"
  type        = string
}

variable "enable_alarm_api_ram" {
  description = "RAM Alarm"
  type        = string
}
