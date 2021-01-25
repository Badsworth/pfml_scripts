# Make the "fineos_eligibility_transfer_lambda_build_s3_key" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional variable during a terraform plan/apply.
variable "fineos_eligibility_transfer_lambda_build_s3_key" {
  description = "S3 key for deployment package for FINEOS eligibility Lambda"
  type        = string
  default     = null
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current_fineos_eligibility_transfer_lambda_build_s3_key" {
  # Don't do a lookup if fineos_eligibility_transfer_lambda_build_s3_key is provided explicitly.
  # This saves some time and also allows us to do a first deploy,
  # where the tfstate file does not yet exist.
  count   = var.fineos_eligibility_transfer_lambda_build_s3_key == null ? 1 : 0
  backend = "s3"

  config = {
    bucket = "massgov-pfml-$ENV_NAME-env-mgmt"
    key    = "terraform/api.tfstate"
    region = "us-east-1"
  }

  defaults = {
    fineos_eligibility_transfer_lambda_build_s3_key = null
  }
}

#  3. Prefer the given variable if provided, otherwise default to the value from last time.
locals {
  fineos_eligibility_transfer_lambda_build_s3_key = (var.fineos_eligibility_transfer_lambda_build_s3_key == null
    ? data.terraform_remote_state.current_fineos_eligibility_transfer_lambda_build_s3_key[0].outputs.fineos_eligibility_transfer_lambda_build_s3_key
  : var.fineos_eligibility_transfer_lambda_build_s3_key)
}

#  4. Store the final value used as a terraform output for next time.
output "fineos_eligibility_transfer_lambda_build_s3_key" {
  value = local.fineos_eligibility_transfer_lambda_build_s3_key
}
