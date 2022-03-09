resource "aws_sns_topic" "sns_resource_changes" {
  name              = "lwd-dfml-itsupport-aws-resource-changes"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

resource "aws_sns_topic_subscription" "sns_resource_changes" {
  topic_arn              = aws_sns_topic.sns_resource_changes.arn
  protocol               = "email"
  endpoint               = "EOL-DL-DFML-ITSUPPORT@MassMail.State.MA.US"
  endpoint_auto_confirms = true
}