locals {
  cloudformation_stack_name = "$ENV_NAME" == "prod" ? "pfml-prod" : "pfml-nonprod"
}

data "aws_vpc" "vpc" {
  tags = {
    "aws:cloudformation:stack-name" = local.cloudformation_stack_name
  }
}

data "aws_subnet_ids" "vpc_app" {
  vpc_id = data.aws_vpc.vpc.id
  tags = {
    Name = "*-Private*"
  }
}
