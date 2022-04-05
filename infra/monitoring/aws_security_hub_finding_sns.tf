resource "aws_sns_topic" "sns_security_hub_finding" {
  name              = "aws-security-hub-findings"
  kms_master_key_id = data.aws_kms_key.main_kms_key.id
}

# Removing Subscription at the request of William Grant due to this spamming the distribution list
# resource "aws_sns_topic_subscription" "sns_security_hub_finding" {
#   topic_arn              = aws_sns_topic.sns_security_hub_finding.arn
#   protocol               = "email"
#   endpoint               = "EOL-DL-SecurityAdvisory@Mass.gov"
#   endpoint_auto_confirms = true
# }