# Configuration for setting up VPC endpoints between our VPCs and AWS services.
# This allows us to connect to certain AWS services directly from our private networks.

# Allow HTTPS traffic from the VPC through the VPC endpoint.
resource "aws_security_group" "vpce" {
  for_each    = toset(local.vpcs)
  name        = "vpce-${each.key}"
  description = "Allow HTTPS inbound traffic from the ${each.key} VPC to VPC endpoints"
  vpc_id      = data.aws_vpc.vpcs[each.key].id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.vpcs[each.key].cidr_block]
  }
}

locals {
  # 1. List out all of the AWS services we rely on from within our private VPCs. Things like Cognito
  #    are not included because we only use it from the Portal or API Gateway, which lives outside our VPCs.
  #
  #    If you want to add new endpoints, you _only_ need to update this list then run terraform apply.
  #
  #    Note: S3 endpoints are required for ECS, but they are already provided as part of EOTSS' AWS account configuration.
  #
  #    ecr.dkr: Pulling app docker images from ECR. We do not need ecr.api because we're using Fargate.
  #    logs:    Sending app logs to cloudwatch.
  #    ssm:     Pulling secrets from Parameter Store.
  #    ec2messages: Required by SSM Parameter Store.
  #
  service_names = ["ecr.dkr", "logs", "ssm", "ec2messages"]

  # 2. Create an object that looks like this:
  #    {
  #      "ecr.dkr/nonprod": {
  #        "service_name": "ecr.dkr",
  #        "vpc_name": "nonprod"
  #      },
  #      "ecr.dkr/prod": { ... },
  #      "logs/nonprod": { ... },
  #      "logs/prod": { ... },
  #      ...
  #    }
  #
  #    We'll use this to generate a VPC Endpoint resource for each VPC + Service Name pair.
  #
  interfaces = { for info in setproduct(local.service_names, local.vpcs) :
    "${info[0]}/${info[1]}" => {
      service_name = data.aws_vpc_endpoint_service.interface_services[info[0]].service_name,
      vpc_name     = info[1]
    }
  }
}

data "aws_vpc_endpoint_service" "interface_services" {
  for_each = toset(local.service_names)
  service  = each.key
}

# 3. Generate a VPC endpoint for each of the pairs we described above in local.interfaces.
#
#    i.e. create a nonprod endpoint and a prod endpoint for every AWS service that we rely on
#    from within our private VPC subnets.
#
resource "aws_vpc_endpoint" "interface_endpoints" {
  for_each          = local.interfaces
  vpc_id            = data.aws_vpc.vpcs[each.value.vpc_name].id
  service_name      = each.value.service_name
  vpc_endpoint_type = "Interface"

  security_group_ids  = [aws_security_group.vpce[each.value.vpc_name].id]
  subnet_ids          = data.aws_subnet_ids.app_private[each.value.vpc_name].ids
  private_dns_enabled = true
}
