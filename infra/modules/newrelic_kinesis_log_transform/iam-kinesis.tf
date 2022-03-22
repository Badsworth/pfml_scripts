#-------------------------------------------------------------------------------------
# Allow Cloudwatch to write to Kinesis Firehose
resource "aws_iam_role" "cloudwatch_writes_to_kinesis" {
  name               = "cloudwatch-writes-to-kinesis"
  assume_role_policy = data.aws_iam_policy_document.cloudwatch_kinesis_role.json
}

data "aws_iam_policy_document" "cloudwatch_kinesis_role" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    principals {
      type = "Service"
      identifiers = [
        "logs.us-east-1.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role_policy" "cloudwatch_writes_to_kinesis" {
  name   = "massgov-pfml-cloudwatch-kinesis-policy"
  role   = aws_iam_role.cloudwatch_writes_to_kinesis.id
  policy = data.aws_iam_policy_document.cloudwatch_kinesis_policy.json
}

data "aws_iam_policy_document" "cloudwatch_kinesis_policy" {
  statement {
    effect = "Allow"
    actions = [
      "firehose:PutRecord",
      "firehose:PutRecordBatch"
    ]
    resources = [
      aws_kinesis_firehose_delivery_stream.kinesis_to_newrelic.arn
    ]
  }
}

#-------------------------------------------------------------------------------------
# Kinesis Firehose to S3 and Cloudwatch, invoke Lambda
resource "aws_iam_role" "kinesis_to_s3" {
  name               = "massgov-pfml-sms-cloudwatch-s3-role"
  assume_role_policy = data.aws_iam_policy_document.kinesis_to_s3_trust.json
}

data "aws_iam_policy_document" "kinesis_to_s3_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = [
        "firehose.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role_policy" "kinesis_to_s3" {
  name   = "massgov-pfml-sms-cloudwatch-s3-policy"
  role   = aws_iam_role.kinesis_to_s3.id
  policy = data.aws_iam_policy_document.kinesis_to_s3.json
}

data "aws_iam_policy_document" "kinesis_to_s3" {
  statement {
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject"
    ]
    resources = [
      aws_s3_bucket.kinesis_to_newrelic_dlq.arn,
      "${aws_s3_bucket.kinesis_to_newrelic_dlq.arn}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
      "lambda:GetFunctionConfiguration"
    ]
    resources = ["${aws_lambda_function.kinesis_filter.arn}:$LATEST"]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:PutLogEvents"
    ]
    resources = ["${aws_cloudwatch_log_group.kinesis_service_logs.arn}:log-stream:*"]
  }
}

#-------------------------------------------------------------------------------------
# Lambda basic execution + kinesis firehose role
resource "aws_iam_role" "lambda_kinesis_executor" {
  name               = "lambda_kinesis_executor"
  assume_role_policy = data.aws_iam_policy_document.lambda_kinesis_executor.json
}
resource "aws_iam_role_policy_attachment" "lambda_kinesis_executor" {
  role = aws_iam_role.lambda_kinesis_executor.name
  # Managed policy, Provides list and read access to Kinesis streams and write permissions to CloudWatch logs.
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole"
}

data "aws_iam_policy_document" "lambda_kinesis_executor" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }

  }
}

#-------------------------------------------------------------------------------------
