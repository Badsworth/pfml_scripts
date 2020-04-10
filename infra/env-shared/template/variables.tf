variable "domain_name" {
  description = "Optional domain name for the API Gateway"
  type        = string
  default     = null
}

variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "nlb_name" {
  description = "Name of the NLB"
  type        = string
}

variable "nlb_vpc_link_name" {
  description = "Name of the VPC Link between NLB and API Gateway"
  type        = string
}

variable "nlb_port" {
  description = "Port of the NLB that will map to the appropriate API"
  type        = string
}
