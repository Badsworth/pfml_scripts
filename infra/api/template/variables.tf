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
