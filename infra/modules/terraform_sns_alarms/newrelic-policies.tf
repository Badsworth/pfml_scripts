# -----------------------------------------------------------------------------
# Low Priority Alerts
# -----------------------------------------------------------------------------

resource "newrelic_alert_channel" "pfml_aws_sns_low_priority_alert" {
  name = local.low_priority_channel_name
  type = "pagerduty"

  config {
    service_key = var.low_priority_nr_integration_key
  }
}

resource "newrelic_alert_policy" "pfml_aws_sns_low_priority_alert" {
  name                = local.low_priority_channel_name
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy_channel" "pfml_aws_sns_low_priority_alert" {
  policy_id = newrelic_alert_policy.pfml_aws_sns_low_priority_alert.id
  channel_ids = [
    newrelic_alert_channel.pfml_aws_sns_low_priority_alert.id
  ]
}

# -----------------------------------------------------------------------------
# High Priority Alerts
# -----------------------------------------------------------------------------

resource "newrelic_alert_channel" "pfml_aws_sns_high_priority_alert" {
  name = local.high_priority_channel_name
  type = "pagerduty"

  config {
    service_key = var.high_priority_nr_integration_key
  }
}

resource "newrelic_alert_policy" "pfml_aws_sns_high_priority_alert" {
  name                = local.high_priority_channel_name
  account_id          = module.constants.newrelic_account_id
  incident_preference = "PER_CONDITION" # a new alarm will sound for every distinct alert condition violated
}

resource "newrelic_alert_policy_channel" "pfml_aws_sns_high_priority_alert" {
  policy_id = newrelic_alert_policy.pfml_aws_sns_high_priority_alert.id
  channel_ids = [
    newrelic_alert_channel.pfml_aws_sns_high_priority_alert.id
  ]
}