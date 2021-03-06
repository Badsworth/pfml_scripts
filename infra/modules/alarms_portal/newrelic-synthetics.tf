locals {
  domain_raw = lookup(module.constants.domains, var.environment_name)
  domain     = var.environment_name == "prod" ? format("https://%s", local.domain_raw) : format("https://%s/?_ff=pfmlTerriyay:true", local.domain_raw)
}

resource "newrelic_synthetics_monitor" "portal_ping" {
  name      = "portal_ping--${var.environment_name}"
  type      = "SIMPLE"
  frequency = 10
  status    = "ENABLED"
  locations = ["AWS_US_EAST_1", "AWS_US_WEST_1"]

  uri = local.domain
  # Validate that this string is on the page
  # SIMPLE synthetics only evaluate the returned HTML and do not
  # execute javascript, so the pmflTerriyay feature flag has no effect
  validation_string = var.environment_name == "prod" ? "apply for Paid Family and Medical Leave" : "Hello world"
}

resource "newrelic_synthetics_monitor" "portal_scripted_browser" {
  name      = "portal_scripted_synthetic--${var.environment_name}"
  type      = "SCRIPT_BROWSER"
  frequency = 10
  status    = "ENABLED"
  locations = ["AWS_US_EAST_1", "AWS_US_WEST_1"]
}

resource "newrelic_synthetics_monitor_script" "portal_browser_script" {
  monitor_id = newrelic_synthetics_monitor.portal_scripted_browser.id
  text = templatefile(
    "${path.module}/uptime.js",
    {
      uri = local.domain
    }
  )
}
