resource "aws_s3_bucket" "document_upload" {
  bucket = "massgov-pfml-${var.environment_name}-document"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  # claimants can only delete and re-upload documents, never update
  versioning {
    enabled = "false"
  }

  tags = merge(module.constants.common_tags, {
    environment = var.environment_name
    public      = "no"
    Name        = "pfml-${var.environment_name}-document-upload"
  })
}

# NB: S3 docs recommend setting these flags at account level
resource "aws_s3_bucket_public_access_block" "lambda_build_block_public_access" {
  bucket = aws_s3_bucket.document_upload.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "document_upload_policy" {
  bucket = aws_s3_bucket.document_upload.id
  policy = data.aws_iam_policy_document.document_upload.json
}

data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}
