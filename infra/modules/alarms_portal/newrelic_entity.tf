# NewRelic Entity file for Portal Alarms 
locals {
  env_prefix = var.environment_name == "cps-preview" ? "CPS-Preview" : upper(var.environment_name)
}

data "newrelic_entity" "pfml-portal" {
  # A reference to the Portal's top-level object in New Relic. Not managed by TF, but required by other Terraform objects.
  name   = "${upper(local.app_name)}-Portal-${local.env_prefix}"
  domain = "BROWSER"
  type   = "APPLICATION"
}