# Make the "cognito_post_confirmation_lambda_artifact_s3_key" variable optional so that "terraform plan"
# and "terraform apply" work without any required variables.
#
# This works as follows:

# 1. Accept an optional variable during a terraform plan/apply.
variable "cognito_post_confirmation_lambda_artifact_s3_key" {
  description = "S3 key for deployment package for Cognito Post Confirmation hook Lambda"
  type        = string
  default     = null
}

#  2. Read the output used from the last terraform state using "terraform_remote_state".
data "terraform_remote_state" "current_cognito_post_confirmation_lambda_artifact_s3_key" {
  # Don't do a lookup if cognito_post_confirmation_lambda_artifact_s3_key is provided explicitly.
  # This saves some time and also allows us to do a first deploy,
  # where the tfstate file does not yet exist.
  count   = var.cognito_post_confirmation_lambda_artifact_s3_key == null ? 1 : 0
  backend = "s3"

  config = {
    bucket = "massgov-pfml-test-env-mgmt"
    key    = "terraform/api.tfstate"
    region = "us-east-1"
  }

  defaults = {
    cognito_post_confirmation_lambda_artifact_s3_key = null
  }
}

#  3. Prefer the given variable if provided, otherwise default to the value from last time.
locals {
  cognito_post_confirmation_lambda_artifact_s3_key = (var.cognito_post_confirmation_lambda_artifact_s3_key == null
    ? data.terraform_remote_state.current_cognito_post_confirmation_lambda_artifact_s3_key[0].outputs.cognito_post_confirmation_lambda_artifact_s3_key
  : var.cognito_post_confirmation_lambda_artifact_s3_key)
}

#  4. Store the final value used as a terraform output for next time.
output "cognito_post_confirmation_lambda_artifact_s3_key" {
  value = local.cognito_post_confirmation_lambda_artifact_s3_key
}
