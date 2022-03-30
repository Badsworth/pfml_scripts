
### Security Hub Findings ###

resource "aws_cloudwatch_event_rule" "security_hub_finding" {
  name          = "alert-on-securityhub-finding"
  description   = "A CloudWatch Event Rule that triggers on AWS Security Hub findings. The Event Rule triggers an email notifications"
  is_enabled    = true
  event_pattern = <<PATTERN
    {
      "source": ["aws.securityhub"],
      "detail-type": ["Security Hub Findings - Imported"],
      "detail": {
        "findings": {
          "AwsAccountId": ["498823821309"],
          "Compliance": {
            "Status": ["FAILED"]
          },
          "RecordState": ["ACTIVE"],
          "Severity": {
            "Label": ["CRITICAL", "HIGH", "MEDIUM"]
          },
          "Workflow": {
            "Status": ["NEW"]
          }
        }
      }
    }
  PATTERN
}

resource "aws_cloudwatch_event_target" "security_hub_finding_sns" {
  rule      = aws_cloudwatch_event_rule.security_hub_finding.name
  target_id = "notify_sns_on_security_hub_finding"
  arn       = var.security_hub_finding_notification_arn
}