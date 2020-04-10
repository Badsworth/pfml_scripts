# Lookup utilities for VPCs.
#
data "aws_vpc" "nava_internal" {
  tags = {
    name = "nava-internal"
  }
}

data "aws_subnet_ids" "nava_internal_app" {
  vpc_id = data.aws_vpc.nava_internal.id
  tags = {
    zone = "app"
  }
}
