resource "aws_sns_topic" "sms_monthly_spend_limit" {
  name              = "${local.prefix}sms-monthly-spend-limit"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

resource "aws_sns_topic" "sms_messages_success_rate" {
  name              = "${local.prefix}sms-messages-success-rate"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

resource "aws_sns_topic" "sms_phone_carrier_unavailable" {
  name              = "${local.prefix}sms-phone-carrier-unavailable"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

resource "aws_sns_topic" "sms_blocked_as_spam" {
  name              = "${local.prefix}sms-blocked-as-spam"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

resource "aws_sns_topic" "sns_sms_rate_exceeded" {
  name              = "${local.prefix}sns-sms-rate-exceeded"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}