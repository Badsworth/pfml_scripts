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
  name               = "sandbox-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = data.aws_subnet_ids.nava_internal_app.ids

  # Even though the load balancer and ECS instances run in the same subnets,
  # an LB instance in zone A cannot route to an ECS instance in zone B unless
  # cross zone load balancing is enabled.
  enable_cross_zone_load_balancing = true
}

# In theory, we could make the one allowed VPC link point to multiple NLBs.
# However, apparently target_arns does not support multiple targets at this time,
# so our nonprod environments rely on the same NLB.
#
# See the env-shared/environments/<env>/main.tf file to see which port it uses
# to proxy the environment's API.
resource "aws_api_gateway_vpc_link" "nlb_vpc_link" {
  name        = "sandbox-nlb-vpc-link"
  description = "VPC link between API gateway and internal network LB"
  target_arns = ["${aws_lb.nlb.arn}"]
}
