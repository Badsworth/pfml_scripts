provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "0.12.20"

  backend "s3" {
    bucket         = "massgov-pfml-sandbox"
    key            = "terraform/vpc.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf_lock"
  }
}

module "pfml" {
  source = "../../template"

  domain_name      = "pfml"
  environment_name = "sandbox"
}
