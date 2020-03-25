provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    aws   = "~> 2.54"
    local = "~> 1.4"
  }
}
