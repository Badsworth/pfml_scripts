# This is the main ECR repo for Nava infra.
# The API server and all the ECS tasks store their Docker images here.
resource "aws_ecr_repository" "api" {
  name = "pfml-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "api_dot_net_1099" {
  name = "pfml-api-dot-net-1099"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "batch_py_1099" {
  name = "pfml-batch-py-1099"

  image_scanning_configuration {
    scan_on_push = true
  }
}
