provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/bi.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.74.1"
    }
  }
}

module "pfml" {
  source = "../../template"

  environment_name                 = "test"
  redshift_daily_import_bucket_key = "80cc3504-457c-4bb0-9d94-fdcf3ddadee1"
}