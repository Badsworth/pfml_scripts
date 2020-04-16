# Make the "service_docker_tag" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional docker_tag variable during a terraform plan/apply.
variable "service_docker_tag" {
  description = "Docker tag of the API release to deploy."
  type        = string
  default     = null
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current" {
  # Don't do a lookup if service_docker_tag is provided explicitly.
  # This saves some time and also allows us to do a first deploy,
  # where the tfstate file does not yet exist.
  count   = var.service_docker_tag == null ? 1 : 0
  backend = "s3"

  config = {
    bucket = "pfml-$ENV_NAME-env-mgmt"
    key    = "terraform/api.tfstate"
    region = "us-east-1"
  }

  defaults = {
    service_docker_tag = null
  }
}

#  3. Prefer the optional docker_tag variable if provided, otherwise default to the docker_tag from last time.
locals {
  service_docker_tag = (var.service_docker_tag == null
    ? data.terraform_remote_state.current[0].outputs.service_docker_tag
    : var.service_docker_tag)
}

#  4. Store the final docker_tag used as a terraform output for next time.
output "service_docker_tag" {
  value = local.service_docker_tag
}
