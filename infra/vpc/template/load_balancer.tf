#
# Terraform configuration for NLB.
#

# Set up a network load balancer within the VPC app subnets.
#
# This load balancer is a bridge between the environment's API Gateway and
# any applications in the VPC that wish to connect to it, using a VPC Link.
#
# Only one VPC link can be used per VPC.
#
# We use a network LB instead of an application LB because they are supported by
# API Gateway VPC links. This allows us to make the network LB internal to the VPC.
resource "aws_lb" "nlb" {
  name               = "${var.environment_name}-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = data.aws_subnet_ids.nava_internal_app.ids

  # Even though the load balancer and ECS instances run in the same subnets,
  # an LB instance in zone A cannot route to an ECS instance in zone B unless
  # cross zone load balancing is enabled.
  enable_cross_zone_load_balancing = true
}

resource "aws_api_gateway_vpc_link" "nlb_vpc_link" {
  name        = "${var.environment_name}-nlb-vpc-link"
  description = "VPC link between API gateway and internal network LB"
  target_arns = ["${aws_lb.nlb.arn}"]
}
