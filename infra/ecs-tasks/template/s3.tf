# Set up a terraform bucket for each environment.
#
locals {
  # When you need a new environment bucket, add your environment name here.
  # The for_each logic below will automagically define your S3 bucket, so you
  # can go straight to running terraform apply.
  environments = ["test", "stage", "prod", "performance"]
}

# Create S3 buckets to load / store ad-hoc verification files
#
# This the location where files to be run in the ad-hoc verification process
# ought to be sourced / loaded from and exported to
#

data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}

resource "aws_s3_bucket" "ad_hoc_verification" {
  for_each = toset(local.environments)
  bucket   = "massgov-pfml-${each.key}-verification-codes"
  acl      = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[each.key]
    Name        = "massgov-pfml-${each.key}-verification-codes"
    public      = "no"
  })
}

resource "aws_s3_bucket" "bulk_user_import" {
  for_each = toset(local.environments)
  bucket   = "massgov-pfml-${each.key}-bulk-user-import"
  acl      = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[each.key]
    Name        = "massgov-pfml-${each.key}-bulk-user-import"
    public      = "no"
  })
}

resource "aws_s3_bucket" "execute_sql_export" {
  for_each = toset(local.environments)
  bucket   = "massgov-pfml-${each.key}-execute-sql-export"
  acl      = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[each.key]
    Name        = "massgov-pfml-${each.key}-execute-sql-export"
    public      = "no"
  })
}

resource "aws_s3_bucket_public_access_block" "verification_codes_block_public_access" {
  for_each = toset(local.environments)
  bucket   = aws_s3_bucket.ad_hoc_verification[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "user_import_block_public_access" {
  for_each = toset(local.environments)
  bucket   = aws_s3_bucket.bulk_user_import[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "sql_export_block_public_access" {
  for_each = toset(local.environments)
  bucket   = aws_s3_bucket.execute_sql_export[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
