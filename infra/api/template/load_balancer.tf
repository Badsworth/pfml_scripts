#
# Terraform configuration for network load balancer.
#

# Set up a network load balancer within the VPC app subnets.
#
# We use a network LB instead of an application LB because they are supported by
# API Gateway VPC links. This allows us to make the network LB internal to the VPC.
resource "aws_lb" "load_balancer" {
  name                             = "${local.app_name}-${var.environment_name}"
  internal                         = true
  load_balancer_type               = "network"
  subnets                          = var.vpc_app_subnet_ids

  # Even though the load balancer and ECS instances run in the same subnets,
  # an LB instance in zone A cannot route to an ECS instance in zone B unless
  # cross zone load balancing is enabled.
  enable_cross_zone_load_balancing = true
}

resource "aws_api_gateway_vpc_link" "nlb_vpc_link" {
  name        = "${local.app_name}-${var.environment_name}-lb-vpc-link"
  description = "VPC link between API gateway and internal network LB"
  target_arns = ["${aws_lb.load_balancer.arn}"]
}

# Forward HTTP traffic to the application.
# Since we're directing traffic from a private API gateway, we don't need to use HTTPS.
resource "aws_lb_listener" "listener" {
  load_balancer_arn = aws_lb.load_balancer.id
  port              = 80
  protocol          = "TCP"

  default_action {
    target_group_arn = aws_lb_target_group.app.id
    type             = "forward"
  }
}

# Define the application target to route HTTP traffic from API Gateway to the API.
resource "aws_lb_target_group" "app" {
  name                 = "${local.app_name}-${var.environment_name}"
  port                 = 80
  protocol             = "TCP"
  vpc_id               = var.vpc_id
  target_type          = "ip"
  deregistration_delay = 20

  health_check {
    protocol            = "HTTP"
    path                = "/"
    healthy_threshold   = var.service_app_count
    unhealthy_threshold = var.service_app_count
  }

  # stickiness is not supported for NLBs, but must be
  # provided due to a terraform-provider-aws bug.
  stickiness {
    enabled = false
    type    = "lb_cookie"
  }
}

output "load_balancer_dns_name" {
  value = aws_lb.load_balancer.dns_name
}
