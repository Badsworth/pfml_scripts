variable "query" {
  description = "Alarm NRQL query. Expected to return a percentage(...)"
  type        = string
}

variable "name" {
  description = "Alarm name"
  type        = string
}

variable "policy_id" {
  description = "Alarm policy ID"
  type        = string
}
