resource "aws_sns_topic" "sns_security_hub_finding" {
  name              = "lwd-dfml-itsupport-aws-security-hub-finding"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

resource "aws_sns_topic_subscription" "sns_security_hub_finding" {
  topic_arn              = aws_sns_topic.sns_security_hub_finding.arn
  protocol               = "email"
  # endpoint               = "EOL-DL-DFML-ITSUPPORT@MassMail.State.MA.US"
  endpoint               = "paz.tursun@mass.gov"
  endpoint_auto_confirms = true
}