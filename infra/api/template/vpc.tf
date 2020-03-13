# Lookup utilities for launching the ECS service and load balancer within a VPC subnet.
#
data "aws_vpc" "vpc" {
  id = var.vpc_id
}

data "aws_subnet" "app" {
  count = "${length(var.vpc_app_subnet_ids)}"
  id    = "${var.vpc_app_subnet_ids[count.index]}"
}
