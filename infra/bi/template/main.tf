module "constants" {
  source = "../../constants"

}

data "aws_caller_identity" "current" {
}

# added for testing