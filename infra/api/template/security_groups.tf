# Security group for the ECS applications. Allows incoming HTTP network traffic
# from the load balancer, and outbound HTTPS traffic to all destinations.
resource "aws_security_group" "app" {
  name        = "${local.app_name}-${var.environment_name}"
  description = "Access for ${title(local.app_name)} ECS service"
  vpc_id      = data.aws_vpc.vpc.id

  # Incoming http from within the VPC and peered VPCs, e.g. the API gateway through the NLB.
  #
  # NLBs act as a pass-through layer, so incoming requests will always look like it's coming
  # from the original source. For this reason, it is not possible to lock down ingress to
  # just the NLB.
  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 1550
    to_port     = 1550
    protocol    = "tcp"
  }

  # Outgoing https to all destinations.
  # TODO(kev): There are many services accessed over https, like ECR and New Relic.
  # Check if we can limit IPs without unreasonable burden on developers and the application.
  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
  }

  # Outgoing UDP/TCP to DHCP servers that are in peer VPCs.
  #
  # This is needed since EOTSS provides us with VPCs that have
  # custom DHCP options, including custom dns servers.
  egress {
    cidr_blocks = ["10.0.0.0/8"]
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
  }

  egress {
    cidr_blocks = ["10.0.0.0/8"]
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
  }
}
