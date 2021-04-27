#
# Terraform configuration for NLBs.
#

# Set up a network load balancer within each VPC's private app subnets.
#
# These load balancers are a bridge between API Gateways and any applications in the VPC
# that wish to connect to those gateways, using a VPC Link instead of public internet.
#
# Only one VPC link can be used per VPC, and only one NLB can be targeted by a VPC Link at this time.
#
# We use a network LB instead of an application LB because they are supported by
# API Gateway VPC links. This allows us to make the network LB internal to the VPC.
resource "aws_lb" "nlbs" {
  for_each           = toset(local.vpcs)
  name               = "${each.key}-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = data.aws_subnet_ids.app_private[each.key].ids

  enable_deletion_protection = true

  # Even though the load balancer and ECS instances run in the same subnets,
  # an LB instance in zone A cannot route to an ECS instance in zone B unless
  # cross zone load balancing is enabled.
  enable_cross_zone_load_balancing = true

  tags = merge(module.constants.common_tags, {
    public = "no"
    Name   = "${each.key}-nlb"
    # nonprod is not a valid environment, so we use stage here.
    environment = each.key == "prod" ? "prod" : "stage"
    "SMX:Asset" = "v1:${each.key}-nlb:${module.constants.smartronix_environment_tags[each.key == "prod" ? "prod" : "stage"]}:NLB:PFML:Advanced:None"
  })
}

# In theory, we could make the one allowed VPC link point to multiple NLBs.
#
# However, target_arns does not support multiple targets at this time,
# so our nonprod environments rely on the same NLB.
#
# See the env-shared/environments/<env>/main.tf file to see which port it uses
# to proxy the environment's API.
resource "aws_api_gateway_vpc_link" "nlb_vpc_links" {
  for_each    = toset(local.vpcs)
  name        = "${each.key}-nlb-vpc-link"
  description = "VPC link between API gateway and internal network LB for ${each.key} VPC"
  target_arns = ["${aws_lb.nlbs[each.key].arn}"]
}
