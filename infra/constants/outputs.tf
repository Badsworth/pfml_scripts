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
    "trn2"        = "trn2"
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
    "trn2"        = "trn2"
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
    "trn2"        = "TRN2"
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
# Note that the EOTSS-recommended format changed to use the `dfml.eol.mass.gov` domain.
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
    "trn2"        = "paidleave-trn2.dfml.eol.mass.gov"
  }
}

output "admin_domains" {
  value = {
    "breakfix"    = "paidleave-admin-breakfix.dfml.eol.mass.gov",
    "cps-preview" = "paidleave-admin-cps-preview.dfml.eol.mass.gov",
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
    "trn2"        = "paidleave-api-trn2.dfml.eol.mass.gov"
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
    "trn2"        = "paidleave-trn2.dfml.eol.mass.gov"
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
    "uat"         = "paidleave-admin-uat.dfml.eol.mass.gov",
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
    "trn2"        = "Training"
  }
}

# Master list of IPs to whitelist for the Admin Portal WAF
output "admin_portal_waf_whitelist" {
  value = [
    "72.234.3.211/32",   # Last Call Media WFH IP
    "86.107.55.213/32",  # Last Call Media WFH IP
    "75.134.71.16/32",   # Last Call Media WFH IP
    "68.204.24.240/32",  # Last Call Media WFH IP - Tyler
    "68.84.12.117/32",   # Last Call Media WFH IP - Niki Ramlogan
    "71.227.169.195/32", # Last Call Media WFH IP - Jessi Murray
    "73.39.112.119/32",  # Last Call Media WFH IP - Jim Ruggiero
    "73.47.218.158/32",  # Chris Griffith WFH
    "47.200.176.201/32", # Ben WFH
    "47.199.161.99/32",  # Jamie WFH
    "76.202.246.67/32",  # Mark WFH
    "70.122.162.186/32", # Jake WFH
    "35.174.218.119/32", # PFML nat-0e7778fcf7a7fc067
    "3.234.51.136/32"    # PFML nat-022bece54348228b5
  ]
}

# High risk country codes to block on WAFs
output "high_risk_country_codes" {
  value = [
    "AF", # Afghanistan
    "DZ", # Algeria
    "BY", # Belarus
    "BI", # Burundi
    "CM", # Cameroon
    "CF", # Central African Republic
    "TD", # Chad
    "CN", # China
    "CO", # Colombia
    "CD", # Democratic Republic of the Congo
    "CU", # Cuba
    "EG", # Egypt
    "SV", # El Savador
    "ER", # Eritrea
    "HT", # Haiti
    "HN", # Honduras
    "HK", # Hong Kong
    "IR", # Iran
    "IQ", # Iraq
    "IL", # Israel
    "KE", # Kenya
    "KP", # Korea (the Democratic People's Republic of)
    "LB", # Lebanon
    "LY", # Libya
    "ML", # Mali
    "MR", # Mauritania
    "MX", # Mexico
    "MM", # Myanmar 
    "NE", # Niger
    "NG", # Nigeria
    "PK", # Pakistan
    "PH", # Philippines
    "RU", # Russia
    "SA", # Saudi Arabia
    "SO", # Somalia
    "SS", # South Sudan
    "SY", # Syria
    "TH", # Thailand
    "UA", # Ukraine
    "VE", # Venezuela
    "YE", # Yemen
    "ZW", # Zimbabwe 
  ]
}

#
# Environments where multi-factor authentication / 2FA should be enabled
#
output "env_mfa_enabled" {
  value = [
    "test",
    "stage",
    "prod",
    "performance",
    "training",
    "uat",
    "breakfix",
    "cps-preview",
    "long",
    "trn2",
    "infra-test"
  ]
}

output "aws_sns_sms_monthly_spend_limit" {
  value = 9180
}

output "newrelic_account_id" {
  description = "PFML's New Relic sub-account number"
  value       = "2837112"
}

output "newrelic_trusted_account_key" {
  description = "EOLWD's New Relic parent account number"
  value       = "1606654"
}
