data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

module "constants" {
  source = "../../constants"
}