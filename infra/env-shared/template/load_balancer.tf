data "aws_api_gateway_vpc_link" "vpc_link" {
  name = var.nlb_vpc_link_name
}

data "aws_lb" "nlb" {
  name = var.nlb_name
}
