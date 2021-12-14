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
      version = "~> 3.66.0"
    }
  }
}

module "pfml" {
  source = "../../template"

  environment_name = "stage"
}                                     