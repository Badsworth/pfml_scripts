resource "aws_s3_bucket" "kinesis_dead_letter_drop" {
  bucket = "massgov-pfml-${var.environment_name}-kinesis-dead-letter-drop"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
    Name        = "pfml-${var.environment_name}-kinesis-dead-letter-drop"
  })

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.kinesis_s3_key.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "kinesis_dead_letter_drop" {
  bucket = aws_s3_bucket.kinesis_dead_letter_drop.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
