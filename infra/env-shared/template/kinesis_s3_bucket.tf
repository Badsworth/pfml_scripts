resource "aws_s3_bucket" "smx_kinesis_firewall_ingest" {
  bucket = "massgov-pfml-${var.environment_name}-smx-kinesis-firewall-ingest"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
    Name        = "pfml-${var.environment_name}-smx-kinesis-firewall-ingest"
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

resource "aws_s3_bucket_public_access_block" "smx_kinesis_firewall_ingest" {
  bucket = aws_s3_bucket.smx_kinesis_firewall_ingest.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
