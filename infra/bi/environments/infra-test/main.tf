provider "aws" {
  region = "us-east-1"
}


terraform {
  required_version = "0.14.7"

  backend "s3" {
    bucket         = "massgov-pfml-infra-test-env-mgmt"
    key            = "terraform/bi.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
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

  environment_name                 = "infra-test"
  redshift_daily_import_bucket_key = "56bb1454-0332-41aa-96eb-9befbe4ff59e"
}
