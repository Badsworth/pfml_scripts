# Make the "cloudfront_origin_path" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional variable during a terraform plan/apply.
variable "cloudfront_origin_path" {
  description = "Key path of the admin portal S3 folder to deploy."
  type        = string
  default     = null
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current_cloudfront_origin_path" {
  # Don't do a lookup if cloudfront_origin_path is provided explicitly.
  # This saves some time and also allows us to do a first deploy,
  # where the tfstate file does not yet exist.
  count   = var.cloudfront_origin_path == null ? 1 : 0
  backend = "s3"

  config = {
    bucket = "massgov-pfml-$ENV_NAME-env-mgmt"
    key    = "terraform/admin-portal.tfstate"
    region = "us-east-1"
  }

  defaults = {
    cloudfront_origin_path = null
  }
}

#  3. Prefer the given variable if provided, otherwise default to the value from last time.
locals {
  cloudfront_origin_path = (var.cloudfront_origin_path == null
    ? data.terraform_remote_state.current_cloudfront_origin_path[0].outputs.cloudfront_origin_path
  : var.cloudfront_origin_path)
}

#  4. Store the final value used as a terraform output for next time.
output "cloudfront_origin_path" {
  value = local.cloudfront_origin_path
}
