resource "newrelic_alert_policy" "sns_alerts" {
  name                = "PFML AWS Account Alerts for SNS"
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy" "low_priority_sns_alerts" {
  name                = "PFML AWS Account Low Priority Alerts for SNS"
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy" "service_desk_alerts" {
  name                = "PFML AWS Account SNS Service Desk Alerts"
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_channel" "newrelic_sns_notifications" {
  name = "PFML AWS Account Alerts channel"
  type = "pagerduty"

  config {
    service_key = var.low_priority_nr_integration_key
  }
}

resource "newrelic_alert_policy_channel" "pfml_sns_alerts" {
  policy_id = newrelic_alert_policy.sns_alerts.id
  channel_ids = [
    newrelic_alert_channel.newrelic_sns_notifications.id
  ]
}

# ------------------------------------------------------------------------------------------------

# This email goes to the service desk and to API on-call engineers.
# If you are on-call, you receive this for visibility and do not need to take action at this time.
# The service desk will reach out as needed with any questions.

resource "newrelic_alert_channel" "newrelic_service_desk_notifications" {
  name = "PFML API Service Desk alerting channel"
  type = "email"

  config {
    recipients              = "EOL-DL-DFML-PFML-SERVICE-DESK@mass.gov, mass-pfml-api-low-priority@navapbc.pagerduty.com"
    include_json_attachment = "true"
  }
}