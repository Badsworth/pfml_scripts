provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    archive = "~> 1.3"
    aws     = "~> 2.54"
  }
}

locals {
  app_name = "pfml-${var.env_name}"
}
