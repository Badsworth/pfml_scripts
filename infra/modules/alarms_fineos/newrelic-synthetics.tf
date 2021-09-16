
resource "newrelic_synthetics_monitor" "fineos_uptime" {
  frequency = 10
  locations = ["AWS_US_EAST_1"]
  name      = "Fineos Uptime/Version Check (${var.environment})"
  status    = "MUTED"
  type      = "SCRIPT_API"
}

resource "newrelic_synthetics_monitor_script" "fineos_uptime" {
  monitor_id = newrelic_synthetics_monitor.fineos_uptime.id
  text = templatefile("${path.module}/uptime.js", {
    TF_ENVIRONMENT_NAME = var.environment
    TF_FINEOS_DOMAIN    = var.fineos_domain
  })
}
