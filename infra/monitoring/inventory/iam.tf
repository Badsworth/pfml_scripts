resource "aws_iam_role" "audit_lambda" {
  name               = "audit_lambda"
  assume_role_policy = data.aws_iam_policy_document.audit_lambda.json
}
resource "aws_iam_role_policy_attachment" "audit_lambda" {
  role = aws_iam_role.audit_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "audit_lambda" {
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