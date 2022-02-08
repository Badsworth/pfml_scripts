variable "kms_key_id" {
  description = "The ID of an AWS managed customer key (CMS)"
  type        = string
  default     = "alias/aws/sns"
}