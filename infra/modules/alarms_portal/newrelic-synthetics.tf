locals {
  domain_raw = lookup(module.constants.domains, var.environment_name)
  domain     = var.environment_name == "prod" ? format("https://%s", local.domain_raw) : format("https://%s/?_ff=pfmlTerriyay:true", local.domain_raw)
}

resource "newrelic_synthetics_monitor" "portal_ping" {
  name      = "portal_ping--${var.environment_name}"
  type      = "SIMPLE"
  frequency = 10
  status    = "ENABLED"
  locations = ["AWS_US_EAST_1"]

  uri = local.domain
  # Validate that this string is on the page
  # SIMPLE synthetics only evaluate the returned HTML and do not
  # execute javascript, so the pmflTerriyay feature flag has no effect
  validation_string = var.environment_name == "prod" ? "Create a worker account" : "Hello world"
}
