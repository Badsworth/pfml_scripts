variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "runtime_py" {
  description = "Pointer to the Python runtime used by the PFML API lambdas"
  type        = string
  default     = "python3.9"
}

variable "redshift_daily_import_bucket_key" {
  description = "KMS Keys for Redshift Daily Import Bucket"
  type        = string
}