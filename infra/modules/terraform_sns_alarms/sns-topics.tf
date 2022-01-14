resource "aws_sns_topic" "sms_monthly_spend_limit" {
  name = "sms-monthly-spend-limit"
}

resource "aws_sns_topic" "sms_messages_success_rate" {
  name = "sms-messages-success-rate"
}

resource "aws_sns_topic" "sms_phone_carrier_unavailable" {
  name = "sms-phone-carrier-unavailable"
}

resource "aws_sns_topic" "sms_blocked_as_spam" {
  name = "sms-blocked-as-spam"
}

resource "aws_sns_topic" "sns_sms_rate_exceeded" {
  name = "sns-sms-rate-exceeded"
}