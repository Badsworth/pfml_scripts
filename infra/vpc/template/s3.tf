# Set up a terraform bucket for applications within this VPC.
#
resource "aws_s3_bucket" "terraform" {
  bucket = "massgov-pfml-${var.environment_name}"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
