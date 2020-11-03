locals {
  vpc = $([ "$ENV_NAME" == "prod" ] && echo '"prod"' || echo '"nonprod"')
}

data "aws_vpc" "vpc" {
  tags = {
    "aws:cloudformation:stack-name" = "pfml-\${local.vpc}"
  }
}

data "aws_subnet_ids" "vpc_app" {
  vpc_id = data.aws_vpc.vpc.id
  tags = {
    Name = "*-Private*"
  }
}

data "aws_subnet_ids" "vpc_db" {
  vpc_id = data.aws_vpc.vpc.id
  tags = {
    Name = "*-DBPrivate*"
  }
}
