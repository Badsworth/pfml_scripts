data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}

data "aws_s3_bucket" "reports" {
  bucket = "massgov-pfml-${var.environment_name}-reports"
}

# TODO (EMPLOYER-1654): Bulk User Import code has been archived. S3 bucket can be removed once its data is removed.
resource "aws_s3_bucket" "bulk_user_import" {
  bucket = "massgov-pfml-${var.environment_name}-bulk-user-import"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-pfml-${var.environment_name}-bulk-user-import"
    public      = "no"
  })
}

resource "aws_s3_bucket" "execute_sql_export" {
  bucket = "massgov-pfml-${var.environment_name}-execute-sql-export"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-pfml-${var.environment_name}-execute-sql-export"
    public      = "no"
  })
}

resource "aws_s3_bucket_public_access_block" "user_import_block_public_access" {
  bucket = aws_s3_bucket.bulk_user_import.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "sql_export_block_public_access" {
  bucket = aws_s3_bucket.execute_sql_export.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
