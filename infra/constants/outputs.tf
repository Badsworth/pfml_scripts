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

# Mapping of different environments/VPC names to EOTSS-mandated AWS tags
output "environment_tags" {
  value = {
    "test"        = "test"
    "stage"       = "stage"
    "prod"        = "prod"
    "nonprod"     = "stage"
    "performance" = "qa"
    "training"    = "train"
  }
}

output "environment_shorthand" {
  value = {
    "test"        = "test"
    "stage"       = "stage"
    "prod"        = "prod"
    "performance" = "perf"
    "training"    = "train"
  }
}

output "smartronix_environment_tags" {
  value = {
    "test"        = "Development"
    "stage"       = "Staging"
    "prod"        = "Production"
    "performance" = "QA"
    "training"    = "Sandbox"
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

output "cert_domains" {
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # as specified in the infra/pfml-aws/acm.tf file.
  value = {
    "test"        = "paidleave-test.mass.gov",
    "stage"       = "paidleave-test.mass.gov",
    "performance" = "paidleave-performance.mass.gov",
    "training"    = "paidleave-performance.mass.gov",
    "prod"        = "paidleave.mass.gov"
  }

}
