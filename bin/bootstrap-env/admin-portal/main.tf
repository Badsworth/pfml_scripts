# This file was originally generated from the following command:
#
#   bin/bootstrap-env/bootstrap-env.sh $ENV_NAME admin-portal
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
    key            = "terraform/admin-portal.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

locals {
  environment_name = "$ENV_NAME"
}

output "cloudfront_distribution_id" {
  description = "Cloudfront distribution id for portal environment. Used for cache invalidation in github workflow."
  value       = module.massgov_pfml.cloudfront_distribution_id
}

module "massgov_pfml" {
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
