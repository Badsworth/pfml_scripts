data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}

data "aws_iam_role" "replication" {
  name = "massgov-pfml-prod-s3-replication"
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

  dynamic "replication_configuration" {
    for_each = var.environment_name == module.constants.bucket_replication_environment ? [1] : []
    content {
      role = data.aws_iam_role.replication.name
      rules {
        id     = "replicateFullBucket"
        status = "Enabled"

        destination {
          bucket        = "arn:aws:s3:::massgov-pfml-${var.environment_name}-reports-replica"
          storage_class = "STANDARD"
          account_id    = "018311717589"
          access_control_translation {
            owner = "Destination"
          }
        }
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "pfml_reports_block_public_access" {
  bucket = aws_s3_bucket.pfml_reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
