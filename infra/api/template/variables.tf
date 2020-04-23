variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "service_app_count" {
  description = "Number of application containers to run"
  type        = number
}

variable "service_docker_tag" {
  description = "Tag of the docker image to run"
  type        = string
}

variable "service_ecs_cluster_arn" {
  description = "ARN of the ECS cluster used to schedule app containers."
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID."
  type        = string
}

variable "vpc_app_subnet_ids" {
  description = "A list of app-level subnets within the VPC."
  type        = list(string)
}

variable "postgres_version" {
  description = "The version of the postgres database."
  type        = string
  default     = "11.6"
}

variable "db_allocated_storage" {
  description = "The allocated storage in gibibytes."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "The upper limit for automatically scaled storage in gibibytes."
  type        = number
  default     = 100
}

variable "db_instance_class" {
  description = "The instance class of the database (RDS)."
  type        = string
  default     = "db.t3.small"
}

variable "db_iops" {
  description = "The amount of provisioned IOPS."
  type        = number
  default     = null
}

variable "db_storage_type" {
  description = "Storage type, one of gp2 or io1."
  type        = string
  default     = "gp2"
}

variable "db_multi_az" {
  description = "Specifies if the RDS instance is multi-AZ."
  type        = bool
  default     = false
}

variable "nlb_name" {
  description = "Name of the network load balancer to route from."
  type        = string
}

variable "nlb_port" {
  description = "Port of the network load balancer that has been reserved within the API Gateway."
  type        = string
}

variable "cors_origins" {
  description = "A list of origins to allow CORS requests from."
  type        = list(string)
}
