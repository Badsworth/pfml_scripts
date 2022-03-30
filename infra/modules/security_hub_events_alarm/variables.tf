
variable "security_hub_finding_notification_arn" {
  description = "aws security hub finding sns topic arn"
  type        = string
  default     = "arn:aws:sns:us-region-1:123456789012:topic_name"
}