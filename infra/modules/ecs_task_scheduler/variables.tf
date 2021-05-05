variable "is_enabled" {
  description = "whether to enable the schedule or not"
  type        = bool
}

variable "cluster_arn" {
  description = "ECS cluster to run the task in"
  type        = string
}

variable "ecs_task_definition_arn" {
  description = "Specific ECS task definition version to launch"
  type        = string
}

variable "ecs_task_definition_family" {
  description = "ECS task definition family"
  type        = string
}

variable "input" {
  description = "Valid JSON text passed to the target as input"
  type        = string
  default     = null
}

variable "app_subnet_ids" {
  description = "Subnets to run the task in"
  type        = list(any)
}

variable "security_group_ids" {
  description = "Security groups for the task to attach"
  type        = list(any)
}

variable "schedule_expression" {
  description = "Schedule to follow for running the task"
  type        = string
}

variable "schedule_name" {
  description = "Name of the schedule"
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
