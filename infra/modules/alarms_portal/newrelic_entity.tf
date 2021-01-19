# NewRelic Entity file for Portal Alarms 

data "newrelic_entity" "pfml-portal" {
  # A reference to the Portal's top-level object in New Relic. Not managed by TF, but required by other Terraform objects.
  name   = "${upper(local.app_name)}-Portal-${upper(var.environment_name)}"
  domain = "BROWSER"
  type   = "APPLICATION"
}