#-----------------------------------------------------------------------------#
#               IAM role for Kinesis Data Firehose                            #
#-----------------------------------------------------------------------------#

# Ref: https://docs.aws.amazon.com/firehose/latest/dev/firehose-dg.pdf#page=52
data "aws_iam_policy_document" "kinesis_aws_waf_policy" {

  depends_on = [
    aws_s3_bucket.smx_kinesis_firewall_ingest
  ]

  # S3 permissions
  statement {
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject"
    ]

    resources = [
      aws_s3_bucket.smx_kinesis_firewall_ingest.arn,
      "${aws_s3_bucket.smx_kinesis_firewall_ingest.arn}/*"
    ]
  }

  # For logging the state of kinesis streams in CloudWatch refer to link above

  # KMS permissions
  statement {
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey"
    ]

    resources = [aws_kms_key.kinesis_s3_key.arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.us-east-1.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:s3:arn"
      values   = ["${aws_s3_bucket.smx_kinesis_firewall_ingest.arn}/*"]
    }
  }
}

data "aws_iam_policy_document" "kinesis_firehose_stream_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["firehose.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "kinesis_aws_waf_role" {
  name               = "mass-pfml-${var.environment_name}-kinesis-aws-waf-role"
  assume_role_policy = data.aws_iam_policy_document.kinesis_firehose_stream_assume_role.json
}

resource "aws_iam_policy" "kinesis_aws_waf_policy" {
  name   = "mass-pfml-${var.environment_name}-kinesis-aws-waf-policy"
  policy = data.aws_iam_policy_document.kinesis_aws_waf_policy.json
}

resource "aws_iam_role_policy_attachment" "kinesis_aws_waf" {
  role       = aws_iam_role.kinesis_aws_waf_role.name
  policy_arn = aws_iam_policy.kinesis_aws_waf_policy.arn
}
