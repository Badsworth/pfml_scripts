# This is to create dependent roles prior to resources that need them

provider "aws" {
  region = "us-east-1"
  }

data "aws_caller_identity" "current" {
}

data "aws_region" "current" {
}

terraform {

    backend "s3" {
    bucket         = "massgov-pfml-test-env-mgmt"
    key            = "terraform/iam.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    kms_key_id     = "arn:aws:kms:us-east-1:498823821309:key/641eba51-98e5-4776-98b6-98ed06866ec8"
    }
}