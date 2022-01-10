data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}
data "aws_s3_bucket" "reports" {
  bucket = "massgov-pfml-${var.environment_name}-reports"
}

data "aws_iam_role" "replication" {
  name = "massgov-pfml-prod-s3-replication"
}

# -------------------------------------------------------------------------
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

  versioning {
    enabled = true
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    Name        = "massgov-pfml-${var.environment_name}-execute-sql-export"
    public      = "no"
  })

  dynamic "replication_configuration" {
    for_each = var.environment_name == module.constants.bucket_replication_environment ? [1] : []
    content {
      role = data.aws_iam_role.replication.arn
      rules {
        id     = "replicateFullBucket"
        status = "Enabled"

        destination {
          bucket        = "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export-replica"
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

resource "aws_s3_bucket_public_access_block" "sql_export_block_public_access" {
  bucket = aws_s3_bucket.execute_sql_export.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for 1099 ECS Tasks usage
resource "aws_s3_bucket" "ecs_tasks_1099_bucket" {
  bucket = "${local.app_name}-${var.environment_name}-1099-form-generator"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = "${var.environment_name}"
    public      = "no"
  })
}

resource "aws_s3_bucket_public_access_block" "ecs_tasks_1099_bucket_block_public_access" {
  bucket = aws_s3_bucket.ecs_tasks_1099_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
