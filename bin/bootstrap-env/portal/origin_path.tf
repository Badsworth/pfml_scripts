# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh $ENV_NAME portal
#
# If making changes, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#

# Make the "cloudfront_origin_path" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional origin_path variable during a terraform plan/apply.
variable "cloudfront_origin_path" {
  description = "Key path of the portal S3 folder to deploy."
  type        = string
  default     = null
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current" {
  count   = var.cloudfront_origin_path == null ? 0 : 1
  backend = "s3"

  config = {
    bucket = "massgov-pfml-$ENV_NAME-env-mgmt"
    key    = "terraform/portal.tfstate"
    region = "us-east-1"
  }

  defaults = {
    cloudfront_origin_path = null
  }
}

#  3. Prefer the optional origin_path variable if provided, otherwise default to the origin path from last time.
locals {
  cloudfront_origin_path = (var.cloudfront_origin_path == null
    ? data.terraform_remote_state.current[0].outputs.cloudfront_origin_path
    : var.cloudfront_origin_path
  )
}

#  4. Store the final origin_path used as a terraform output for next time.
output "cloudfront_origin_path" {
  value = local.cloudfront_origin_path
}
