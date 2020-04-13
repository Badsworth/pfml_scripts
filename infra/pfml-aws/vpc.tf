# Search for VPCs and subnets pre-created by EOTSS.
#
locals {
  vpcs = ["nonprod", "prod"]
}

data "aws_vpc" "vpcs" {
  for_each = toset(local.vpcs)

  tags = {
    "aws:cloudformation:stack-name" = "pfml-${each.key}"
  }
}

data "aws_subnet_ids" "app_private" {
  for_each = toset(local.vpcs)

  vpc_id = data.aws_vpc.vpcs[each.key].id
  tags = {
    Name = "*-Private*"
  }
}
