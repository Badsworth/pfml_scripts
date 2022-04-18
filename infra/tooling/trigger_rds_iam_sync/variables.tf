variable "secret_token_arn" {
  type        = string
  description = "arn for ssm parameter that contains github token"
}

variable "prefix" {
  type        = string
  description = "naming convention prefix"
}

variable "rds_cluster_arns" {
  type        = list
  description = "source arns for rds cluster"
}