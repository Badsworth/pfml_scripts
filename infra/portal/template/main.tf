provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    archive = "~> 1.3"
    aws     = "~> 2.57"
  }
}

locals {
  app_name = "pfml"
}
