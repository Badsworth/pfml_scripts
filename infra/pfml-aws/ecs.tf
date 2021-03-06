# This is the main ECR repo for Nava infra.
# The API server and all the ECS tasks store their Docker images here.
resource "aws_ecr_repository" "api" {
  name = "pfml-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}
# Additional ECR repo for PDF API images
resource "aws_ecr_repository" "pdf_api" {
  name = "pfml-pdf-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}