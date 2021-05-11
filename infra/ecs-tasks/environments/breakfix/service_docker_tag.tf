# Make the "service_docker_tag" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional variable during a terraform plan/apply.
variable "service_docker_tag" {
  description = "Docker tag of the API release to associate with ECS tasks."
  type        = string
  default     = null
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current_service_docker_tag" {
  # Don't do a lookup if service_docker_tag is provided explicitly.
  # This saves some time and also allows us to do a first deploy,
  # where the tfstate file does not yet exist.
  count   = var.service_docker_tag == null ? 1 : 0
  backend = "s3"

  config = {
    bucket = "massgov-pfml-breakfix-env-mgmt"
    key    = "terraform/ecs-tasks.tfstate"
    region = "us-east-1"
  }

  defaults = {
    service_docker_tag = null
  }
}

#  3. Prefer the given variable if provided, otherwise default to the value from last time.
locals {
  service_docker_tag = (var.service_docker_tag == null
    ? data.terraform_remote_state.current_service_docker_tag[0].outputs.service_docker_tag
  : var.service_docker_tag)
}

#  4. Store the final value used as a terraform output for next time.
output "service_docker_tag" {
  value = local.service_docker_tag
}
