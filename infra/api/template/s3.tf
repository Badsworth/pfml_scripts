# Temporary feature gate storage bucket
resource "aws_s3_bucket" "feature_gate" {
  bucket = "massgov-pfml-${var.environment_name}-feature-gate"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  versioning {
    enabled = "false"
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    public      = "no"
    Name        = "pfml-${var.environment_name}-feature-gate"
  })
}

resource "aws_s3_bucket" "business_intelligence_tool" {
  bucket = "massgov-pfml-${var.environment_name}-business-intelligence-tool"
  acl    = "private"

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name],
    public      = "no"
    Name        = "massgov-pfml-${var.environment_name}-BI-tool"
  })
}

resource "aws_s3_bucket_public_access_block" "business_intelligence_tool" {
  bucket = aws_s3_bucket.business_intelligence_tool.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_s3_bucket" "agency_transfer" {
  bucket = "massgov-pfml-${var.environment_name}-agency-transfer"
}

data "aws_s3_bucket" "terraform" {
  bucket = "massgov-pfml-${var.environment_name}-env-mgmt"
}

data "aws_s3_bucket" "mass_pfml_acct_mgmt" {
  bucket = "massgov-pfml-aws-account-mgmt"
}

