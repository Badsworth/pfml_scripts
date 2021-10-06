data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}

resource "aws_s3_bucket" "pfml_reports" {
  bucket = "massgov-pfml-${var.environment_name}-reports"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  versioning {
    enabled = "true"
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
    Name        = "massgov-pfml-${var.environment_name}-reports"
  })
}

resource "aws_s3_bucket_public_access_block" "pfml_reports_block_public_access" {
  bucket = aws_s3_bucket.pfml_reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
