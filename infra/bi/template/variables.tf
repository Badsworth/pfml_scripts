variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "runtime_py" {
  description = "Pointer to the Python runtime used by the PFML API lambdas"
  type        = string
  default     = "python3.9"
}