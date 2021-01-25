# Allow RDS access from the ECS tasks.
resource "aws_security_group_rule" "rds_postgresql_ingress_ecs_tasks" {
  type                     = "ingress"
  description              = "PostgreSQL from ad-hoc ECS tasks"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.tasks.id
  security_group_id        = data.aws_security_group.rds_postgresql.id
}


# Security group for the ECS applications. Allows incoming HTTP network traffic
# from the load balancer, and outbound HTTPS traffic to all destinations.
resource "aws_security_group" "tasks" {
  name        = "${local.app_name}-${var.environment_name}-tasks"
  description = "Access for ${title(local.app_name)} ECS tasks"
  vpc_id      = var.vpc_id

  # Outgoing https to all destinations.
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
    security_groups = [data.aws_security_group.rds_postgresql.id]
  }

  # MMARS Data Mart connection
  egress {
    cidr_blocks = ["10.0.0.0/8"]
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
  }

  # MOVEit connection
  egress {
    cidr_blocks = ["10.0.0.0/8"]
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
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
