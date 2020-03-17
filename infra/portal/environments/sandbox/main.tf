provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "~> 0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-sandbox"
    key            = "terraform/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf_lock"
  }
}

output "cloudfront_distribution_id" {
  value       = module.massgov_pfml.cloudfront_distribution_id
  description = "Cloudfront distribution id for portal environment. Used for cache invalidation in github workflow."
}

module "massgov_pfml" {
  source                      = "../../template"
  env_name                    = "sandbox-v2"
  cognito_extra_redirect_urls = ["http://localhost:3000"]
  cognito_extra_logout_urls   = ["http://localhost:3000"]
  portal_s3_bucket_name       = "mpfml-prototype"
  cloudfront_origin_path      = local.cloudfront_origin_path
}
