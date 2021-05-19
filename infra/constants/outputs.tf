output "common_tags" {
  value = {
    agency        = "dfml"
    application   = "pfml"
    businessowner = "anthony.fantasia@state.ma.us"
    createdby     = "ma-pfml-alerts@mass.gov"
    itowner       = "anthony.fantasia@state.ma.us"
    secretariat   = "eolwd"
  }
}

output "newrelic_log_ingestion_arn" {
  value = "arn:aws:lambda:us-east-1:498823821309:function:newrelic-log-ingestion"
}

# Mapping of different environments/VPC names to EOTSS-mandated AWS tags.
#
# NOTE: This needs to be approved from the list of tags in
#       https://lwd.atlassian.net/wiki/spaces/DD/pages/272072807/Tagging+Standards.
output "environment_tags" {
  value = {
    "test"        = "test"
    "stage"       = "stage"
    "prod"        = "prod"
    "nonprod"     = "stage"
    "performance" = "qa"
    "training"    = "train"
    "uat"         = "uat"
    "breakfix"    = "qa"
    "cps-preview" = "qa"
    "adhoc"       = "test"
  }
}

# Mapping of environments to shorthand names for resources with a small max length,
# such as IAM role names.
#
# The maximum length here is five characters.
#
output "environment_shorthand" {
  value = {
    "test"        = "test"
    "stage"       = "stage"
    "prod"        = "prod"
    "performance" = "perf"
    "training"    = "train"
    "uat"         = "uat"
    "breakfix"    = "bfx"
    "cps-preview" = "cpspr"
  }
}

output "smartronix_environment_tags" {
  value = {
    "test"        = "Development"
    "stage"       = "Staging"
    "prod"        = "Production"
    "performance" = "QA"
    "training"    = "Sandbox"
    "uat"         = "UAT"
    "breakfix"    = "Breakfix"
    "cps-preview" = "CPSPreview"
    "adhoc"       = "Adhoc"
  }
}

output "prod_admin_roles" {
  value = [
    "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
    "arn:aws:iam::498823821309:role/AWS-498823821309-Infrastructure-Admin",
    "arn:aws:iam::498823821309:role/ci-run-deploys",
  ]
}

output "nonprod_admin_roles" {
  value = [
    "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
    "arn:aws:iam::498823821309:role/AWS-498823821309-Infrastructure-Admin",
    "arn:aws:iam::498823821309:role/ci-run-deploys",
    "arn:aws:iam::498823821309:role/AWS-498823821309-NonPROD-Admins",
  ]
}

# Mapping of environments to pretty domains
output "domains" {
  value = {
    "test"        = "paidleave-test.mass.gov",
    "stage"       = "paidleave-stage.mass.gov",
    "performance" = "paidleave-performance.mass.gov",
    "training"    = "paidleave-training.mass.gov",
    "breakfix"    = "paidleave-breakfix.eol.mass.gov",
    "cps-preview" = "paidleave-cps-preview.eol.mass.gov",
    "uat"         = "paidleave-uat.mass.gov",
    "prod"        = "paidleave.mass.gov"
  }
}

output "api_domains" {
  value = {
    "test"        = "paidleave-api-test.mass.gov",
    "stage"       = "paidleave-api-stage.mass.gov",
    "performance" = "paidleave-api-performance.mass.gov",
    "training"    = "paidleave-api-training.mass.gov",
    "breakfix"    = "paidleave-api-breakfix.eol.mass.gov",
    "cps-preview" = "paidleave-api-cps-preview.eol.mass.gov",
    "uat"         = "paidleave-api-uat.mass.gov",
    "prod"        = "paidleave-api.mass.gov"
  }
}

# Mapping of environments to certificate domain lookups
output "cert_domains" {
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # that is specified in the certificate.
  value = {
    "test"        = "paidleave-test.mass.gov",
    "stage"       = "paidleave-test.mass.gov",
    "performance" = "paidleave-performance.mass.gov",
    "training"    = "paidleave-performance.mass.gov",
    "breakfix"    = "paidleave-breakfix.eol.mass.gov",
    "cps-preview" = "paidleave-breakfix.eol.mass.gov",
    "uat"         = "paidleave-uat.mass.gov",
    "prod"        = "paidleave.mass.gov"
  }

}
