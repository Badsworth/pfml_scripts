
resource "newrelic_synthetics_monitor" "fineos_version_watcher" {
  frequency = 10
  locations = ["AWS_US_EAST_1"]
  name      = "Fineos Uptime/Version Check (${var.environment})"
  status    = "MUTED"
  type      = "SCRIPT_API"
}

resource "newrelic_synthetics_monitor_script" "fineos_version_watcher" {
  monitor_id = newrelic_synthetics_monitor.fineos_version_watcher.id
  text       = <<EOD
/**
 * This synthetic check lives in Terraform.
 *
 * Do not edit this script in New Relic.
 */
const config = {
    fineos_url: "${var.fineos_url}",
    environment: "${var.environment}"
}
${file("${path.module}/uptime.js")}
EOD
}
