# This file was originally generated from the following command:
#
#   bin/bootstrap-env.sh $ENV_NAME portal
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
    bucket         = "massgov-pfml-$ENV_NAME-env-mgmt"
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
  cognito_extra_redirect_urls = []
  cognito_extra_logout_urls   = []
  cognito_enable_provisioned_concurrency = false

  # Firewall rules
  # 'true' will set rule to 'BLOCK' (or 'NONE' which is equivalent)
  # 'false' will set rule to 'COUNT' (counts traffic that meets rule(s) instead of blocking)
  enforce_cloudfront_rate_limit     = true
  enforce_cloudfront_fortinet_rules = true
  
  # You probably don't need to change the variables below:
  source                 = "../../template"
  environment_name       = "$ENV_NAME"
  cloudfront_origin_path = local.cloudfront_origin_path
}
