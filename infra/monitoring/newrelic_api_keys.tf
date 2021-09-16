# Terraform code for managing New Relic secrets from AWS SSM. These are used to configure the NewRelic provider.
# These params have been manually stored in SSM and are not managed through Terraform.
# moved to PD

# Personal API key tied to a single user. NB: replace this key if Ada ever leaves.
data "aws_ssm_parameter" "newrelic-api-key" {
  name = "/admin/pfml-api/newrelic-api-key"
}

data "aws_ssm_parameter" "newrelic-admin-api-key" {
  name = "/admin/pfml-api/newrelic-admin-api-key"
}

locals {
  fineos_urls = {
    "test" : "https://dt2-claims-webapp.masspfml.fineos.com"
    "stage" : "https://idt-claims-webapp.masspfml.fineos.com"
    "performance" : "https://perf-claims-webapp.masspfml.fineos.com"
    "training" : "https://trn-claims-webapp.masspfml.fineos.com"
    "cps-preview" : "https://dt3-claims-webapp.masspfml.fineos.com"
    // Note: Intentionally omitting UAT and prod for the moment due to SSO requirements.
  }
}

module "fineos" {
  for_each    = toset(keys(local.fineos_urls))
  source      = "../modules/alarms_fineos"
  environment = each.key
  fineos_url  = local.fineos_urls[each.key]
}
