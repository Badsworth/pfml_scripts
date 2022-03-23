# ----------------------------------------------------------------------------------------------------------------------
# Bucket for Kinesis Firehose to New Relic DLQ
resource "aws_s3_bucket" "kinesis_to_newrelic_dlq" {
  bucket = var.dlq_bucket_name

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
  tags = {
    environment = "prod"
    public      = "no"
    Name        = var.dlq_bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "kinesis_to_newrelic_dlq" {
  bucket                  = aws_s3_bucket.kinesis_to_newrelic_dlq.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------------
