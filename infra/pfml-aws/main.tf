provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-aws-account-mgmt"
    key            = "terraform/aws.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform_locks"
    encrypt        = "true"
  }
}
