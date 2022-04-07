resource "aws_iam_policy_document" "iam_refresh_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# IAM Role for lambda
resource "aws_iam_role" "iam_refresh" {
  name               = "rds-iam-refresh-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.iam_refresh_trust_policy.json
  inline_policy {
    name = "lambda-get-parameter"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action   = "ssm:GetParameter"
          Effect   = "Allow"
          Resource = data.aws_ssm_parameter.iam_refresh.arn
        },
      ]
    })
  }
}

# Allow lambda to create logs

resource "aws_iam_role_policy_attachment" "wokoro-iam_refresh" {
  role = aws_iam_role.wokoro-iam_refresh.name
  # Managed policy, granting permission to upload logs to CloudWatch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}