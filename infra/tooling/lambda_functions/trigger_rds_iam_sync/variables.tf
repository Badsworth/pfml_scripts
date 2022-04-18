variable "secret_token_arn" {
  type        = string
  description = "arn for ssm parameter that contains github token"
}

variable "prefix" {
  type        = string
  description = "naming convention prefix"
}

variable "rds_cluster_arn" {
  type        = string
  description = "source arn for rds cluster"
}