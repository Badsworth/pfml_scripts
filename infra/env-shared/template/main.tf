provider "aws" {
  region = "us-east-1"
  alias  = "us-east-1"
}

terraform {
  required_version = "0.12.24"
}
