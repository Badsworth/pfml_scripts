variable "alarm_name" {
  description = "Name of the alarm"
  type        = string
}

variable "where_span_filter" {
  description = "WHERE filter for endpoint based on Span attributes"
  type        = string
}

variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "policy_id" {
  description = "ID of the New Relic alerts policy to attach to"
  type        = string
}
