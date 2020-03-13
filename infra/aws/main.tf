provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-global"
    key            = "terraform/aws.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf_lock"
  }
}
