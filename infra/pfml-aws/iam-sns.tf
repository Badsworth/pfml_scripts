# Allows the SNS topic "pfml-bounced-rejected-emails-topic", which is subscribed to bounce and complaint events
# from our noreplypfml@mass.gov SES address, to write these events to Kinesis Data Firehose for ingestion by New Relic.
# Assignment of these roles/policies to SNS entities cannot currently be managed in Terraform.

locals {
  # Neither of these are currently used in Terraform, but keep them here anyway for possible future use.
  sns_kinesis_topic_arn       = "arn:aws:sns:us-east-1:498823821309:pfml-bounced-rejected-emails-topic"
  sns_kinesis_subscription_id = "dfc61c4f-25ab-4a39-bf46-faa86849ab1a"
}

resource "aws_iam_role" "ses_bounces_and_complaints_to_kinesis" {
  name               = "massgov-pfml-ses-newrelic"
  assume_role_policy = data.aws_iam_policy_document.sns_assume_role_boilerplate.json
}

resource "aws_iam_role_policy_attachment" "allow_sns_writes_to_kinesis" {
  role       = aws_iam_role.ses_bounces_and_complaints_to_kinesis.name
  policy_arn = aws_iam_policy.allow_sns_writes_to_kinesis.arn
}

resource "aws_iam_policy" "allow_sns_writes_to_kinesis" {
  name   = "massgov-pfml-ses-newrelic"
  policy = data.aws_iam_policy_document.allow_sns_writes_to_kinesis.json
}

data "aws_iam_policy_document" "allow_sns_writes_to_kinesis" {
  # Allows data to be written to our Kinesis stream for ingestion by New Relic.
  statement {
    effect    = "Allow"
    actions   = ["firehose:PutRecord", "firehose:PutRecordBatch"]
    resources = [aws_kinesis_firehose_delivery_stream.ses_to_newrelic.arn]
  }

  # Allows SNS to call CloudWatch Logs on our behalf.
  # Derives from manual set-up of this policy and its role in the AWS console.
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutMetricFilter",
      "logs:PutRetentionPolicy"
    ]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "sns_assume_role_boilerplate" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM Role to allow SNS text messages to write to CloudWatch Logs.
# This role was originally created in the console. Bringing it over to Terraform

resource "aws_iam_role" "sns_sms_deliveries" {
  name               = "massgov-pfml-sns-sms-deliveries"
  assume_role_policy = data.aws_iam_policy_document.sns_assume_role_boilerplate.json
}

resource "aws_iam_role_policy_attachment" "allow_sns_writes_to_cloudwatch" {
  role       = aws_iam_role.sns_sms_deliveries.name
  policy_arn = aws_iam_policy.allow_sns_writes_to_cloudwatch.arn
}

resource "aws_iam_policy" "allow_sns_writes_to_cloudwatch" {
  name   = "massgov-pfml-sns-sms-deliveries"
  policy = data.aws_iam_policy_document.allow_sns_writes_to_cloudwatch.json
}

data "aws_iam_policy_document" "allow_sns_writes_to_cloudwatch" {
  # Allows SNS to call CloudWatch Logs on our behalf.
  # Derives from manual set-up of this policy and its role in the AWS console.
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutMetricFilter",
      "logs:PutRetentionPolicy"
    ]
    resources = ["*"]
  }
}