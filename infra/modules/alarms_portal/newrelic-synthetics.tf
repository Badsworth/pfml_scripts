locals {
  domains = {
    "${var.environment_name}" = "https://paidleave-${var.environment_name}.mass.gov/?_ff=pfmlTerriyay:true"
    "prod"                    = "https://paidleave.mass.gov"
  }
  domain = lookup(local.domains, var.environment_name)
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
  validation_string = var.environment_name == "prod" ? "Create an account" : "Hello world"
}

resource "newrelic_synthetics_monitor" "portal_scripted_browser" {
  name      = "portal_scripted_login--${var.environment_name}"
  type      = "SCRIPT_BROWSER"
  frequency = 10
  status    = "ENABLED"
  locations = ["AWS_US_EAST_1"]
}

resource "newrelic_synthetics_monitor_script" "portal_browser_script" {
  monitor_id = newrelic_synthetics_monitor.portal_scripted_browser.id
  text = templatefile(
    "${path.module}/newrelic-scripted-monitor.js",
    {
      uri = local.domain
    }
  )
}
