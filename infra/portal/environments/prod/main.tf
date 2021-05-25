# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh prod portal
#
# If adding new variables, it's recommended to update the bootstrap
# templates so there's less manual work in creating new envs.
#
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-prod-env-mgmt"
    key            = "terraform/portal.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
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
  cognito_extra_redirect_urls            = []
  cognito_extra_logout_urls              = []
  cognito_enable_provisioned_concurrency = true

  # Firewall rules
  # 'true' will set rule to 'BLOCK' (or 'NONE' which is equivalent)
  # 'false' will set rule to 'COUNT' (counts traffic that meets rule(s) instead of blocking)
  enforce_cloudfront_rate_limit     = true
  enforce_cloudfront_fortinet_rules = true

  # You probably don't need to change the variables below:
  source                 = "../../template"
  environment_name       = "prod"
  cloudfront_origin_path = local.cloudfront_origin_path
}
