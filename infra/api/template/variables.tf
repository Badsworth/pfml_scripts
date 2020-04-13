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
}

variable "nlb_name" {
  description = "Name of the network load balancer to route from."
  type        = string
}

variable "nlb_port" {
  description = "Port of the network load balancer that has been reserved within the API Gateway."
  type        = string
}
