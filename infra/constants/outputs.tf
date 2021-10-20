# Tags that should be attached and consistent across resources.
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

# The ARN for the lambda function which forwards logs from Cloudwatch to New Relic.
# This lambda function was manually set up in the AWS console and services all environments.
output "newrelic_log_ingestion_arn" {
  value = "arn:aws:lambda:us-east-1:498823821309:function:newrelic-log-ingestion"
}

# The ARN of the new AWS-managed SSO profile for Infra-Admins.
output "infra_admin_sso_arn" {
  value = "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-infrastructure-admin_9049548fba1c97b7"
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

# Mapping of environments to Smartronix-supported values.
# These values are referenced in the Smartronix CAMS monitoring harness to set up AWS-centric alarms.
#
# Read more about CAMS (Cloud Assured Managed Services) here:
# https://www.smartronix.com/services/cloud-computing/managed-services.html
#
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

# List of roles that signify production-level access.
output "prod_admin_roles" {
  value = [
    "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
    "arn:aws:iam::498823821309:role/ci-run-deploys",
    "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-infrastructure-admin_9049548fba1c97b7"
  ]
}

# List of roles that signify nonproduction-level access.
output "nonprod_admin_roles" {
  value = [
    "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
    "arn:aws:iam::498823821309:role/ci-run-deploys",
    "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-infrastructure-admin_9049548fba1c97b7",
    "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-nonprod-admins_d9b2995c1106dfbb"
  ]
}

# Mapping of environments to pretty domains.
# Note that the EOTSS-recommended format changed to use the eol.mass.gov domain.
#
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

# Mapping of human-readable names to the unique channel ID.
# We prefer to use the channel ID in case the channel name changes in Slack.
#
# Note that the human-readable name here does not need to match the Slack channel name.
#
output "slackbot_channels" {
  value = {
    "mass-pfml-pd-warnings" = "C01GTDGBR0F"
  }
}
