data "aws_iam_policy_document" "security_hub_finding_sns_topic_policy" {
  statement {
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [var.security_hub_finding_notification_arn]
  }
}

resource "aws_sns_topic_policy" "default" {
  arn    = var.security_hub_finding_notification_arn
  policy = data.aws_iam_policy_document.security_hub_finding_sns_topic_policy.json
}