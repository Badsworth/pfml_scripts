variable "prefix" {
  type        = string
  description = "The prefix to use for all auditors"
  default     = "audit"
}

variable "tags" {
  type        = map(any)
  description = "Tags to use"
}

variable "region" {
  type        = string
  description = "The AWS region to use"
}

variable "aws_account_id" {
  type        = string
  description = "The AWS Account to use"
}

variable "schedule" {
  type        = string
  description = "Schedule for the auditors to run"
}