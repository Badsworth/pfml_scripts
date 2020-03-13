resource "aws_ecr_repository" "api" {
  name = "pfml-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECS cluster for running sandboxed applications.
#
# Applications within this cluster are not actually tied
# to the sandbox VPC, but we separate them to improve
# organization and simplify lookups.
resource "aws_ecs_cluster" "cluster" {
  name = "sandbox"

  setting {
    name = "containerInsights"
    value = "enabled"
  }
}
