# Set up a terraform bucket for each environment.
#
locals {
  # When you need a new environment bucket, add your environment name here.
  # The for_each logic below will automagically define your S3 bucket, so you
  # can go straight to running terraform apply.
  environments = ["test", "stage"]
}

resource "aws_s3_bucket" "terraform" {
  for_each = toset(local.environments)

  bucket = "massgov-pfml-${each.key}-env-mgmt"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  versioning {
    enabled = "true"
  }

  tags = {
    agency        = "eol"
    application   = "coreinf"
    businessowner = "kevin.yeh@mass.gov"
    createdby     = "kevin.yeh@mass.gov"
    environment   = each.key
    itowner       = "kevin.yeh@mass.gov"
    public        = "no"
    secretariat   = "eolwd"
    Name          = "pfml-${each.key}-env-mgmt"
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_block_public_access" {
  for_each = aws_s3_bucket.terraform
  bucket   = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
