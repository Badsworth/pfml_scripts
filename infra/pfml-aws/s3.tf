# Set up a terraform bucket for each environment.
#
locals {
  # When you need a new environment bucket, add your environment name here.
  # The for_each logic below will automagically define your S3 bucket, so you
  # can go straight to running terraform apply.
  environments = ["test"]
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
