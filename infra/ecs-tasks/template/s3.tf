data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}

# Create S3 buckets to load / store ad-hoc verification files
#
# This the location where files to be run in the ad-hoc verification process
# ought to be sourced / loaded from and exported to
#
resource "aws_s3_bucket" "ad_hoc_verification" {
  bucket = "massgov-pfml-${var.environment_name}-verification-codes"
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
    Name        = "massgov-pfml-${var.environment_name}-verification-codes"
    public      = "no"
  })
}

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

resource "aws_s3_bucket_public_access_block" "verification_codes_block_public_access" {
  bucket = aws_s3_bucket.ad_hoc_verification.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
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
