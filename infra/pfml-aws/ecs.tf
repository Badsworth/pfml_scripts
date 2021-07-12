# This is the main ECR repo for Nava infra.
# The API server and all the ECS tasks store their Docker images here.
resource "aws_ecr_repository" "api" {
  name = "pfml-api"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# This repo stores third-party Docker images that were (manually) mirrored from DockerHub.
# It exists to help us bypass DockerHub's strict rate limits for unpaid/unregistered user accounts,
# which allows third-party 'sidecar' images to be reliably incorporated into ECS task builds.
resource "aws_ecr_repository" "dockerhub_mirror" {
  name = "eolwd-pfml-dockerhub-mirror"

  tags = {
    purpose = "AWS-hosted mirror for third-party DockerHub images"
  }
}
