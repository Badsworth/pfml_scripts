variable "ecs_task_definition_family" {
  description = "ECS task definition family"
  type        = string
}

variable "app_subnet_ids" {
  description = "Subnets to run the task in"
  type        = list(any)
}

variable "task_name" {
  description = "Name of the task"
  type        = string
}

variable "environment_name" {
  description = "Name of the environment to run in"
  type        = string
}

variable "ecs_task_executor_role" {
  description = "Execution role that must be passed to the ECS task"
  type        = string
}

variable "ecs_task_role" {
  description = "Task role that must be passed to the ECS task"
  type        = string
  default     = null
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket that will be triggering this lambda"
  type        = string
}

variable "security_group_ids" {
  description = "Security groups for the ECS task to run with"
  type        = list(any)
}
