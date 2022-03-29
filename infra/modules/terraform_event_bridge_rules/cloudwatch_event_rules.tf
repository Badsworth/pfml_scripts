resource "aws_cloudwatch_event_rule" "ec2_state_change" {
  name          = "ec2_state_change"
  description   = "Notify when an EC2 instance changes state"
  event_pattern = <<EOF
{
  "detail-type": [
    "EC2 Instance State-change Notification"
  ]
}
EOF
}

resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.ec2_state_change.name
  target_id = "notify_sns_on_ec2_state_change"
  arn       = var.sns_topic_arn
}

### Security Hub Findings ###

resource "aws_cloudwatch_event_rule" "security_hub_finding" {
  name = "alert-on-securityhub-finding"
  description = "A CloudWatch Event Rule that triggers on AWS Security Hub findings. The Event Rule triggers an email notifications"
  is_enabled = true
  event_pattern = <<PATTERN
    {
      "detail-type": [
        "Security Hub Findings - Imported"
      ],
      "detail": {
        "findings": {
          "Severity": {
            "Label": ["CRITICAL", "HIGH", "MEDIUM"]
          }
        }
      },
      "source": [
        "aws.securityhub"
      ]
    }
  PATTERN
}

resource "aws_cloudwatch_event_target" "security_hub_finding_sns" {
  rule = aws_cloudwatch_event_rule.security_hub_finding.name
  target_id = "notify_sns_on_security_hub_finding"
  arn = var.security_hub_finding_notification_arn
}