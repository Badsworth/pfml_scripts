variable "enabled" {
  description = "Whether the alarm is enabled or not"
  default     = true
}

variable "name" {
  description = "Name of the alarm"
}

variable "nrql" {
  description = "NRQL query to trigger an alarm on"
}

variable "policy_id" {
  description = "New Relic policy for the alarm to attach to"
}

variable "runbook_url" {
  description = "URL of the runbook for this alarm"
  default     = null
}

variable "fill_option" {
  description = "Value to fill for windows with no data points."
  default     = "last_value"
}
