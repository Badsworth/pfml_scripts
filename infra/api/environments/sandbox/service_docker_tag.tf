# Make the "service_docker_tag" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional docker_tag variable during a terraform plan/apply.
variable "service_docker_tag" {
  description = "Docker tag of the API release to deploy."
  type        = string
  default     = ""
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current" {
  backend = "s3"

  config = {
    bucket = "massgov-pfml-sandbox"
    key    = "terraform/api.tfstate"
    region = "us-east-1"
  }

  defaults = {
    service_docker_tag = ""
  }
}

#  3. Prefer the optional docker_tag variable if provided, otherwise default to the docker_tag from last time.
locals {
  service_docker_tag = coalesce(
    var.service_docker_tag,
    data.terraform_remote_state.current.outputs.service_docker_tag
  )
}

#  4. Store the final docker_tag used as a terraform output for next time.
output "service_docker_tag" {
  value = local.service_docker_tag
}
