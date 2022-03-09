resource "aws_sns_sms_preferences" "update_sms_prefs" {
  # Additionally, this must be set in AWS Pinpoint (manually through the console).
  # Service limit increase support tickets must be opened for both SNS and Pinpoint.
  monthly_spend_limit = module.constants.aws_sns_sms_monthly_spend_limit

  delivery_status_iam_role_arn          = aws_iam_role.sns_sms_deliveries.arn
  delivery_status_success_sampling_rate = 100
  default_sender_id                     = "pfml"
  default_sms_type                      = "Transactional"
  usage_report_s3_bucket                = aws_s3_bucket.sns_sms_usage_reports.id
}