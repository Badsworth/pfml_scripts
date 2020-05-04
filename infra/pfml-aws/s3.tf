# Set up a terraform bucket for each environment.
#
locals {
  # When you need a new environment bucket, add your environment name here.
  # The for_each logic below will automagically define your S3 bucket, so you
  # can go straight to running terraform apply.
  environments = ["test", "stage", "prod"]
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

# Create S3 buckets to receive agency data.
#
# Note that we're creating more buckets than agencies will be interacting with.
# Here, we're creating one for each environment, as well as one "nonprod" bucket
# for data will be sent ad-hoc for initial verification and whenever we need to
# verify format changes.
#
# Since agencies like DOR do not have recurring non-PII test data, we cannot use
# them as our main data sources for lower environments. Instead, they sent real
# data to prod and ad-hoc data to nonprod, which we can feed other lower environments.
#
# In day-to-day operations, we'll likely be generating our own mock data to feed into
# lower environments.
#
resource "aws_s3_bucket" "agency_transfer" {
  for_each = toset(concat(local.environments, local.vpcs))
  bucket   = "massgov-pfml-${each.key}-agency-transfer"
  acl      = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    agency        = "eol"
    application   = "coreinf"
    businessowner = "kevin.yeh@mass.gov"
    createdby     = "kevin.yeh@mass.gov"
    environment   = each.key == "nonprod" ? "stage" : each.key
    itowner       = "kevin.yeh@mass.gov"
    public        = "no"
    secretariat   = "eolwd"
    Name          = "massgov-pfml-agency-transfer-dor-${each.key}"
  }
}

resource "aws_s3_bucket_public_access_block" "agency_transfer_block_public_access" {
  for_each = toset(concat(local.environments, local.vpcs))
  bucket   = aws_s3_bucket.agency_transfer[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

