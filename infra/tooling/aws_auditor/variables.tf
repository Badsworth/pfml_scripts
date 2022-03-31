variable "prefix" {
  type        = string
  description = "The prefix to use for all auditors"
  default     = "audit"
}

variable "auditors" {
  type        = map(string)
  description = "The mapping of auditors and actions to use"
}

variable "tags" {
  type        = map(string)
  description = "Tags to use"
}