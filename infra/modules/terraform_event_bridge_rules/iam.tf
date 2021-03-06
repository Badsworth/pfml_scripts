data "aws_iam_policy_document" "resource_change_sns_topic_policy" {
  statement {
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [var.sns_topic_arn]
  }
}

resource "aws_sns_topic_policy" "default" {
  arn    = var.sns_topic_arn
  policy = data.aws_iam_policy_document.resource_change_sns_topic_policy.json
}