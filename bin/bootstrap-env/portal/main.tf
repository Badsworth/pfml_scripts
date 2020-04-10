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
  required_version = "~> 0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-$ENV_NAME-env-mgmt"
    key            = "terraform/portal.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
}

output "cloudfront_distribution_id" {
  value       = module.massgov_pfml.cloudfront_distribution_id
  description = "Cloudfront distribution id for portal environment. Used for cache invalidation in github workflow."
}

module "massgov_pfml" {
  source                 = "../../template"
  env_name               = "$ENV_NAME"
  cognito_sender_email   = null
  cognito_use_ses_email  = false
  portal_s3_bucket_name  = "pfml-portal-builds"
  cloudfront_origin_path = local.cloudfront_origin_path
}
