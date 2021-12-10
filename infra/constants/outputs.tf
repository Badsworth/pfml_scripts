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
    "adhoc"       = "test"
    "breakfix"    = "qa"
    "cps-preview" = "qa"
    "infra-test"  = "test"
    "long"        = "test"
    "nonprod"     = "stage"
    "performance" = "qa"
    "prod"        = "prod"
    "stage"       = "stage"
    "test"        = "test"
    "training"    = "train"
    "uat"         = "uat"
  }
}

# Mapping of environments to shorthand names for resources with a small max length,
# such as IAM role names.
#
# The maximum length here is five characters.
#
output "environment_shorthand" {
  value = {
    "breakfix"    = "bfx"
    "cps-preview" = "cpspr"
    "infra-test"  = "itest"
    "long"        = "long"
    "performance" = "perf"
    "prod"        = "prod"
    "stage"       = "stage"
    "test"        = "test"
    "training"    = "train"
    "uat"         = "uat"
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
    "adhoc"       = "Adhoc"
    "breakfix"    = "Breakfix"
    "cps-preview" = "CPSPreview"
    "infra-test"  = "Sandbox"
    "long"        = "LONG"
    "prod"        = "Production"
    "performance" = "QA"
    "stage"       = "Staging"
    "test"        = "Development"
    "training"    = "Sandbox"
    "uat"         = "UAT"
  }
}

# List of roles that signify production-level access.
output "prod_admin_roles" {
  value = [
    "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
    "arn:aws:iam::498823821309:role/ci-run-deploys",
    "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-infrastructure-admin_9049548fba1c97b7",
    "arn:aws:iam::498823821309:role/ADFS-Admin"
  ]
}

# List of roles that signify nonproduction-level access.
output "nonprod_admin_roles" {
  value = [
    "arn:aws:iam::498823821309:role/AWS-498823821309-CloudOps-Engineer",
    "arn:aws:iam::498823821309:role/ci-run-deploys",
    "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-infrastructure-admin_9049548fba1c97b7",
    "arn:aws:iam::498823821309:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_eolwd-pfml-nonprod-admins_d9b2995c1106dfbb",
    "arn:aws:iam::498823821309:role/ADFS-Admin"
  ]
}

# Mapping of environments to pretty domains.
# Note that the EOTSS-recommended format changed to use the eol.mass.gov domain.
#
output "domains" {
  value = {
    "breakfix"    = "paidleave-breakfix.eol.mass.gov",
    "cps-preview" = "paidleave-cps-preview.eol.mass.gov",
    "long"        = "paidleave-long.dfml.eol.mass.gov"
    "performance" = "paidleave-performance.mass.gov",
    "prod"        = "paidleave.mass.gov",
    "infra-test"  = "paidleave-infra-test.dfml.eol.mass.gov",
    "stage"       = "paidleave-stage.mass.gov",
    "test"        = "paidleave-test.mass.gov",
    "training"    = "paidleave-training.mass.gov",
    "uat"         = "paidleave-uat.mass.gov",
  }
}

output "admin_domains" {
  value = {
    "breakfix"    = "paidleave-admin-breakfix.dfml.eol.mass.gov",
    "cps-preview" = "paidleave-admin-cpspreview.dfml.eol.mass.gov",
    "infra-test"  = "paidleave-admin-infra-test.dfml.eol.mass.gov",
    "long"        = "paidleave-admin-long.dfml.eol.mass.gov",
    "performance" = "paidleave-admin-performance.dfml.eol.mass.gov",
    "prod"        = "paidleave-admin.dfml.eol.mass.gov",
    "stage"       = "paidleave-admin-stage.dfml.eol.mass.gov",
    "test"        = "paidleave-admin-test.dfml.eol.mass.gov",
    "training"    = "paidleave-admin-training.dfml.eol.mass.gov",
    "trn2"        = "paidleave-admin-trn2.dfml.eol.mass.gov"
    "uat"         = "paidleave-admin-uat.dfml.eol.mass.gov",
  }
}

output "api_domains" {
  value = {
    "breakfix"    = "paidleave-api-breakfix.eol.mass.gov",
    "cps-preview" = "paidleave-api-cps-preview.eol.mass.gov",
    "infra-test"  = "paidleave-api-infra-test.dfml.eol.mass.gov",
    "long"        = "paidleave-api-long.dfml.eol.mass.gov"
    "performance" = "paidleave-api-performance.mass.gov",
    "prod"        = "paidleave-api.mass.gov",
    "stage"       = "paidleave-api-stage.mass.gov",
    "test"        = "paidleave-api-test.mass.gov",
    "training"    = "paidleave-api-training.mass.gov",
    "uat"         = "paidleave-api-uat.mass.gov",
  }
}

# Mapping of environments to certificate domain lookups
output "cert_domains" {
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # that is specified in the certificate.
  value = {
    "breakfix"    = "paidleave-breakfix.eol.mass.gov",
    "cps-preview" = "paidleave-breakfix.eol.mass.gov",
    "infra-test"  = "paidleave-infra-test.dfml.eol.mass.gov",
    "long"        = "paidleave-long.dfml.eol.mass.gov"
    "performance" = "paidleave-performance.mass.gov",
    "prod"        = "paidleave.mass.gov",
    "stage"       = "paidleave-test.mass.gov",
    "test"        = "paidleave-test.mass.gov",
    "training"    = "paidleave-performance.mass.gov",
    "uat"         = "paidleave-uat.mass.gov",
  }
}

# Mapping of admin portal environments to certificate domain lookups
output "admin_portal_cert_domains" {
  # you cannot lookup certs by a SAN, so we lookup based on the first domain
  # that is specified in the certificate.
  value = {
    "breakfix"    = "paidleave-admin-breakfix.dfml.eol.mass.gov",
    "cps-preview" = "paidleave-admin-cps-preview.dfml.eol.mass.gov",
    "infra-test"  = "paidleave-admin-infra-test.dfml.eol.mass.gov",
    "long"        = "paidleave-admin-long.dfml.eol.mass.gov",
    "performance" = "paidleave-admin-performance.dfml.eol.mass.gov",
    "prod"        = "paidleave-admin.dfml.eol.mass.gov",
    "stage"       = "paidleave-admin-stage.dfml.eol.mass.gov",
    "training"    = "paidleave-admin-training.dfml.eol.mass.gov"
    "trn2"        = "paidleave-admin-trn2.dfml.eol.mass.gov",
    "test"        = "paidleave-admin-test.dfml.eol.mass.gov",
    "uat"         = "paidleave-admin-test.dfml.eol.mass.gov",
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

output "bucket_replication_environment" {
  value = "test"
}

# Env Var mappings for ECS Tasks
# Currently only used in aws_ecs_task_definition.ecs_tasks_1099 resource
output "env_var_mappings" {
  value = {
    "breakfix"    = "Breakfix"
    "cps-preview" = "CPSPreview"
    "infra-test"  = "Test"
    "long"        = "Long"
    "performance" = "Performance"
    "prod"        = "Production"
    "stage"       = "Staging"
    "test"        = "Test"
    "training"    = "Training"
    "uat"         = "UAT"
  }
}

# Master list of IPs to whitelist for the Admin Portal WAF
output "admin_portal_waf_whitelist" {
  value = [
    "72.234.3.211/32",   # Last Call Media WFH IP
    "86.107.55.213/32",  # Last Call Media WFH IP
    "75.134.71.16/32",   # Last Call Media WFH IP
    "47.200.176.201/32", # Ben WFH
    "47.199.161.99/32",  # Jamie WFH
    "10.206.0.0/21",     # LWD
    "10.203.236.0/24"    # PFML
  ]
}
