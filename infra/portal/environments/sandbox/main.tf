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

locals {
  domain = "pfml-sandbox-v2.navateam.com"
  tld    = "navateam.com"
}

output "cloudfront_distribution_id" {
  value = module.massgov_pfml.cloudfront_distribution_id
}

module "massgov_pfml" {
  source                      = "../../template"
  domain                      = local.domain
  environment_name            = "sandbox-v2"
  cloudfront_certificate_arn  = data.aws_acm_certificate.domain.arn
  cognito_extra_redirect_urls = ["http://localhost:3000", "https://${local.domain}"]
  cognito_extra_logout_urls   = ["http://localhost:3000", "https://${local.domain}"]
  cognito_sender_email        = null
  cognito_use_ses_email       = false
  portal_s3_bucket_name       = "mpfml-prototype"
  cloudfront_origin_path      = local.cloudfront_origin_path
}
