provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-stage-env-mgmt"
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

  environment_name                 = "stage"
  redshift_daily_import_bucket_key = "c83f6468-f34d-44e6-93d3-24690aca4b5a"
}