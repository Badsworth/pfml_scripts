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

  # Outgoing PostgreSQL to RDS.
  egress {
    description     = "PostgreSQL to RDS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.rds_postgresql.id]
  }

  # Outgoing UDP/TCP to DNS servers that are in peer VPCs.
  #
  # This is needed since EOTSS provides us with VPCs that have
  # custom DNS options, including custom dns servers.
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

# Security group for the RDS instance.
#
# Note: this group uses the standalone aws_security_group_rule format instead of the inline format, to avoid a
# cyclic dependency between this group and aws_security_group.app.
resource "aws_security_group" "rds_postgresql" {
  name        = "${local.app_name}-rds-${var.environment_name}"
  description = "Access for ${title(local.app_name)} RDS database"
  vpc_id      = data.aws_vpc.vpc.id

  lifecycle {
    create_before_destroy = true
  }
}

# Disallow outbound network connections.
# We can't explicitly deny outbound access, but can override the default allow-all egress rule by making a more
# limited one.
resource "aws_security_group_rule" "rds_postgresql_egress_none" {
  type              = "egress"
  description       = "Deny all egress"
  from_port         = 0
  to_port           = 0
  protocol          = "tcp"
  cidr_blocks       = ["127.0.0.1/32"]
  security_group_id = aws_security_group.rds_postgresql.id
}

# Allow RDS access from the ECS applications.
resource "aws_security_group_rule" "rds_postgresql_ingress_app" {
  type                     = "ingress"
  description              = "PostgreSQL from ECS applications"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
  security_group_id        = aws_security_group.rds_postgresql.id
}

# Allow RDS access from the Smartronix Nessus scanners.
resource "aws_security_group_rule" "rds_postgresql_ingress_nessus" {
  type              = "ingress"
  description       = "PostgreSQL from Smartronix Nessus"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = ["172.21.1.0/27"]
  security_group_id = aws_security_group.rds_postgresql.id
}

# Allow RDS access from AWS Workspaces.
# The source SG is managed by EOTSS / Smartronix.
resource "aws_security_group_rule" "rds_postgresql_ingress_workspaces" {
  type                     = "ingress"
  description              = "PostgreSQL from AWS Workspaces"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = "sg-01b132e682b7aa99b"
  security_group_id        = aws_security_group.rds_postgresql.id
}
