provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
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

  domain_name       = aws_api_gateway_domain_name.domain_name.domain_name
  environment_name  = "sandbox"
  nlb_name          = "sandbox-nlb"
  nlb_vpc_link_name = "sandbox-nlb-vpc-link"
  nlb_port          = "80"
}
