# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pfml-insights-copy-files
# ----------------------------------------------------------------------------------------------------------------------
data "aws_s3_bucket" "business_intelligence_tool" {
  bucket = "massgov-pfml-${var.environment_name}-business-intelligence-tool"
}
resource "aws_iam_role_policy" "pfml_insights_copy_files_role_policy" {
  name   = "pfml-api-${var.environment_name}-bi-copy-files-role-policy"
  role   = aws_iam_role.bi_reporting_lambda_role.id
  policy = data.aws_iam_policy_document.insights_copy_files_role_policy_document.json
}

data "aws_iam_policy_document" "insights_copy_files_role_policy_document" {
  statement {
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*"
    ]

    resources = [
      data.aws_s3_bucket.business_intelligence_tool.arn,
      "${data.aws_s3_bucket.business_intelligence_tool.arn}/*"
    ]

    effect = "Allow"
  }
  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload",
      "s3:ListBucket",
      "s3:List*"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-redshift-daily-import",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-redshift-daily-import/*"
    ]

    effect = "Allow"
  }

  statement {
    actions = [
      "kms:Decrypt"
    ]

    resources = [
      "arn:aws:kms:us-east-1:498823821309:key/${var.redshift_daily_import_bucket_key}"
    ]

    effect = "Allow"
  }
}