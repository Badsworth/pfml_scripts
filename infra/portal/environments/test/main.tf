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
  required_version = "0.12.24"

  backend "s3" {
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/portal.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

locals {
  app_name         = "pfml"
  environment_name = "test"
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

output "storybook_url" {
  value = aws_s3_bucket.storybook.website_endpoint
}

module "massgov_pfml" {
  cognito_extra_redirect_urls            = ["http://localhost:3000"]
  cognito_extra_logout_urls              = ["http://localhost:3000"]
  cognito_enable_provisioned_concurrency = false

  # Firewall rules
  # 'true' will set rule to 'BLOCK' (or 'NONE' which is equivalent)
  # 'false' will set rule to 'COUNT' (counts traffic that meets rule(s) instead of blocking)
  enforce_cloudfront_rate_limit     = true
  enforce_cloudfront_fortinet_rules = true

  # You probably don't need to change the variables below:
  source                 = "../../template"
  environment_name       = local.environment_name
  cloudfront_origin_path = local.cloudfront_origin_path
}

module "constants" {
  source = "../../../constants"
}
