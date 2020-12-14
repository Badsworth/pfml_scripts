resource "aws_kms_key" "kinesis_s3_key" {
  description             = "KMS key to encrypt/decrypt data in kinesis s3 bucket"
  deletion_window_in_days = 7
}

resource "aws_kms_alias" "kinesis_s3_key_alias" {
  name          = "alias/mass-pfml-${var.environment_name}-kinesis-s3-key"
  target_key_id = aws_kms_key.kinesis_s3_key.key_id
}
