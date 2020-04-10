resource "aws_ecr_repository" "api" {
  name = "paid-leave-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}
