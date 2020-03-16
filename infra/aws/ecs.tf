resource "aws_ecr_repository" "api" {
  name = "pfml-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}
