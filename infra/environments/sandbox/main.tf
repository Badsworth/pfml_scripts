provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "~> 0.12.19"

  backend "s3" {
    bucket         = "massgov-pfml-sandbox"
    key            = "terraform/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf_lock"
  }
}

module "massgov_pfml" {
  source               = "../../template"
  env_name             = "sandbox-v2"
  cognito_redirect_url = "http://localhost:3000"
  cognito_logout_url   = "http://localhost:3000"
}

