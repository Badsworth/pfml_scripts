# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh test portal
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "~> 0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/portal.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

output "cloudfront_distribution_id" {
  description = "Cloudfront distribution id for portal environment. Used for cache invalidation in github workflow."
  value       = module.massgov_pfml.cloudfront_distribution_id
}

output "cognito_user_pool_id" {
  value = module.massgov_pfml.cognito_user_pool_id
}

output "cognito_user_pool_client_id" {
  value = module.massgov_pfml.cognito_user_pool_client_id
}

module "massgov_pfml" {
  # Once you have a domain name, update the following variables:
  # domain = "pfml-test.eolwd.mass.gov"
  cognito_extra_redirect_urls = ["http://localhost:3000"]
  cognito_extra_logout_urls   = ["http://localhost:3000"]

  # Change the variables below if this environment should send Cognito emails through SES:
  cognito_sender_email  = null
  cognito_use_ses_email = false

  # You probably don't need to change the variables below:
  source                 = "../../template"
  environment_name       = "test"
  portal_s3_bucket_name  = "massgov-pfml-test-portal-site-builds"
  cloudfront_origin_path = local.cloudfront_origin_path
}
