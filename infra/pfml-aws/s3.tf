# Set up a terraform bucket for each environment.
#
locals {
  # When you need a new environment bucket, add your environment name here and to
  # the environment_tags output in infra/constants/outputs.tf.
  #
  # The for_each logic below will automagically define your S3 bucket, so you
  # can go straight to running terraform apply.
  environments = ["test", "stage", "prod", "performance", "training", "uat", "breakfix", "cps-preview", "adhoc", "smx-cognito-restore"]
}

# ----------------------------------------------------------------------------------------------------------------------

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

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[each.key]
    public      = "no"
    Name        = "pfml-${each.key}-env-mgmt"
  })
}

resource "aws_s3_bucket_public_access_block" "terraform_block_public_access" {
  for_each = aws_s3_bucket.terraform
  bucket   = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------------

# Create S3 buckets to store data imported from Formstack

resource "aws_s3_bucket" "formstack_import" {
  for_each = toset(local.environments)

  bucket = "massgov-pfml-${each.key}-formstack-data"
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

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[each.key]
    public      = "no"
    Name        = "massgov-pfml-${each.key}-formstack-data"
  })
}

resource "aws_s3_bucket_public_access_block" "formstack_import_block_public_access" {
  for_each = aws_s3_bucket.formstack_import
  bucket   = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------------

# Create S3 buckets to receive agency data.
#
# Note that we're creating more buckets than agencies will be interacting with.
# Here, we're creating one for each environment, as well as one "nonprod" bucket
# for data will be sent ad-hoc for initial verification and whenever we need to
# verify format changes.
#
# Since agencies like DOR do not have recurring non-PII test data, we cannot use
# them as our main data sources for lower environments. Instead, they send real
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

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[each.key]
    Name        = "massgov-pfml-${each.key}-agency-transfer"
    public      = "no"
  })
}

resource "aws_s3_bucket_public_access_block" "agency_transfer_block_public_access" {
  for_each = toset(concat(local.environments, local.vpcs))
  bucket   = aws_s3_bucket.agency_transfer[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_s3_bucket" "lambda_build" {
  bucket = "massgov-pfml-api-lambda-builds"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = "prod"
    public      = "no"
    Name        = "massgov-pfml-api-lambda-builds"
  })
}

resource "aws_s3_bucket_public_access_block" "lambda_build_block_public_access" {
  bucket = aws_s3_bucket.lambda_build.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------------

# Create S3 buckets to store CSVs that will be linked in emails sent to
# Third-Party Administrators (TPAs)

resource "aws_s3_bucket" "tpa_csv_storage" {
  bucket = "massgov-pfml-tpa-csv-storage"
  acl    = "private"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(module.constants.common_tags, {
    environment = "prod"
    public      = "no"
    Name        = "massgov-pfml-tpa-csv-storage"
  })
}

resource "aws_s3_bucket_public_access_block" "tpa_csv_storage_block_public_access" {
  bucket = aws_s3_bucket.tpa_csv_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ----------------------------------------------------------------------------------------------------------------------

resource "aws_s3_bucket" "ses_to_newrelic_dlq" {
  bucket = "massgov-pfml-ses-to-newrelic-dlq"
  tags = merge(module.constants.common_tags, {
    environment = "prod"
    public      = "no"
    Name        = "massgov-pfml-ses-to-newrelic-dlq"
  })

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "aws:kms"
        kms_master_key_id = aws_kms_key.ses_newrelic_dlq.arn
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ses_to_newrelic_dlq" {
  bucket                  = aws_s3_bucket.ses_to_newrelic_dlq.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
