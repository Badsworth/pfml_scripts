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
