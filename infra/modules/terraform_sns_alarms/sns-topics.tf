resource "aws_sns_topic" "sms_monthly_spend_limit" {
  name              = "sms-monthly-spend-limit"
  kms_master_key_id = var.kms_key_id
}

resource "aws_sns_topic" "sms_messages_success_rate" {
  name              = "sms-messages-success-rate"
  kms_master_key_id = var.kms_key_id
}

resource "aws_sns_topic" "sms_phone_carrier_unavailable" {
  name              = "sms-phone-carrier-unavailable"
  kms_master_key_id = var.kms_key_id
}

resource "aws_sns_topic" "sms_blocked_as_spam" {
  name              = "sms-blocked-as-spam"
  kms_master_key_id = var.kms_key_id
}

resource "aws_sns_topic" "sns_sms_rate_exceeded" {
  name              = "sns-sms-rate-exceeded"
  kms_master_key_id = var.kms_key_id
}