
provider "aws" {
  region = "us-east-1"
}
terraform {
  required_providers {
    aws     = "3.74.1"
  }
}
data "aws_ssm_parameter" "rds-iam-refresh" {
  name  = "rds-iam_refresh"
  type  = "String"
  value = "Hello World"
}

output "rds-iam-refresh" {
  value = data.aws_ssm_parameter.rds-iam-refresh.id
}

