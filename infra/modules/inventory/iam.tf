data "aws_iam_policy_document" "auditor_iam_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "auditor_inventory_policy" {
  for_each = locals.auditors
  statement {
    actions   = ["dynamodb:PutItem"]
    effect    = "Allow"
    resources = ["arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${aws_dynamodb_table.inventory[each.key].name}"]
  }
}

data "aws_iam_policy_document" "auditor_policy" {
  for_each = local.auditors
  statement {
    actions   = each.value["actions"]
    effect    = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_role" "audit" {
  for_each           = local.auditors
  name               = "massgov_pfml_audit_${each.key}_role"
  assume_role_policy = data.aws_iam_policy_document.auditor_iam_trust_policy.json
}

resource "aws_iam_role_policy_attachment" "audit" {
  for_each   = local.auditors
  role       = aws_iam_role.audit[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}