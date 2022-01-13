# IAM roles and permissions for ECS tasks.

locals {
  ssm_arn_prefix = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/service"
}

data "aws_iam_policy_document" "ecs_tasks_assume_role_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Task runtime role. This role is used by the task after it has started up -- i.e. for application-level access to AWS resources.
resource "aws_iam_role" "ecs_tasks" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks"

  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# Task execution role. This role is used by ECS during startup to pull container images from
# ECR and access secrets from Systems Manager Parameter Store before running the application.
#
# See: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
resource "aws_iam_role" "task_executor" {
  name = "${local.app_name}-${var.environment_name}-ecs-tasks-execution-role"

  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

data "aws_iam_policy_document" "task_executor" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin/*",
      "${local.ssm_arn_prefix}/${local.app_name}/common/*"
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin",
      "${local.ssm_arn_prefix}/${local.app_name}/common"
    ]
  }
}

# Link access policies to the ECS task execution role.
resource "aws_iam_role_policy" "task_executor" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-execution-role-policy"
  role   = aws_iam_role.task_executor.id
  policy = data.aws_iam_policy_document.task_executor.json
}

# ------------------------------------------------------------------------------------------------------
# Execute SQL Export Task Stuff
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "task_execute_sql_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-execute-sql-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

data "aws_iam_policy_document" "task_sql_export_s3_policy_doc" {
  # Allow Execute SQL task access to WRITE S3 files
  statement {
    actions = [
      "s3:PutObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export/*",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-business-intelligence-tool/api_db/accounts_created",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-business-intelligence-tool/api_db/accounts_created/*"
    ]
  }
}

resource "aws_iam_policy" "task_execute_sql_s3_policy" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-execute-sql-s3-policy"
  description = "Policy for accessing S3 files Execute SQL Tasks"
  policy      = data.aws_iam_policy_document.task_sql_export_s3_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "task_execute_sql_s3_attachment" {
  role       = aws_iam_role.task_execute_sql_task_role.name
  policy_arn = aws_iam_policy.task_execute_sql_s3_policy.arn
}

# ------------------------------------------------------------------------------------------------------
# Register Leave Admins with FINEOS
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "register_admins_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-register-admins-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "register_admins_task_role_policy_attachment" {
  role       = aws_iam_role.register_admins_task_role.name
  policy_arn = aws_iam_policy.register_admins_task_policy.arn
}

resource "aws_iam_policy" "register_admins_task_policy" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-register-admins-task-policy"
  description = "A clone of the standard task role with extra SSM permissions for FINEOS auth keys."
  policy      = data.aws_iam_policy_document.register_admins_task_role_policy_document.json
}

data "aws_iam_policy_document" "register_admins_task_role_policy_document" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common/*",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin/*"
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin"
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]

    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-feature-gate",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-feature-gate/*"
    ]

  }
}


# ------------------------------------------------------------------------------------------------------
# DOR Import task stuff
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "dor_import_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "dor_import_task_role_extras" {
  role       = aws_iam_role.dor_import_task_role.name
  policy_arn = aws_iam_policy.dor_import_task_role_extras.arn
}

resource "aws_iam_policy" "dor_import_task_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-ecs-policy"
  description = "All the things the DOR Import task needs to be allowed to do"
  policy      = data.aws_iam_policy_document.dor_import_task_role_extras.json
}

data "aws_iam_policy_document" "dor_import_task_role_extras" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

resource "aws_iam_role" "dor_import_execution_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "dor_import_execution_role_extras" {
  role       = aws_iam_role.dor_import_execution_role.name
  policy_arn = aws_iam_policy.dor_import_execution_role_extras.arn
}

resource "aws_iam_policy" "dor_import_execution_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-dor-import-execution-policy"
  description = "A clone of the standard execution role with extra SSM permissions for DOR Import's decryption keys."
  policy      = data.aws_iam_policy_document.dor_import_execution_role_extras.json
}

data "aws_iam_policy_document" "dor_import_execution_role_extras" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common/*",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin/*"
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}-dor-import/${var.environment_name}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin"
    ]
  }
}

# ------------------------------------------------------------------------------------------------------
# DOR Pending Filing Submission File task stuff
# ------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "dor_pending_filing_sub_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-dor_pending_filing_sub-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "dor_pending_filing_sub_task_role_extras" {
  role       = aws_iam_role.dor_pending_filing_sub_task_role.name
  policy_arn = aws_iam_policy.dor_pending_filing_sub_task_role_extras.arn
}

resource "aws_iam_policy" "dor_pending_filing_sub_task_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-dor_pending_filing_sub-ecs-policy"
  description = "All the things the DOR Pending Filing Submision File task needs to be allowed to do"
  policy      = data.aws_iam_policy_document.dor_pending_filing_sub_task_role_extras.json
}

data "aws_iam_policy_document" "dor_pending_filing_sub_task_role_extras" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for FINEOS Eligibility Feed export
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "fineos_eligibility_feed_export_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-eligibility-feed-export"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "fineos_eligibility_feed_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-eligibility-feed-export-fineos-policy"
  role   = aws_iam_role.fineos_eligibility_feed_export_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for FINEOS employee updates import
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "fineos_import_employee_updates_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-employee-updates"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "fineos_import_employee_updates_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-employee-updates-fineos-policy"
  role   = aws_iam_role.fineos_import_employee_updates_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

data "aws_iam_policy_document" "fineos_feeds_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  statement {

    effect = "Allow"

    actions = [
      "sts:AssumeRole",
    ]

    resources = [
      var.fineos_aws_iam_role_arn,
    ]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for FINEOS import leave admin org units
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "fineos_import_la_org_units_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-la-org-units"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "fineos_import_la_org_units_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-la-org-units-fineos-policy"
  role   = aws_iam_role.fineos_import_la_org_units_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pub-payments-process-fineos
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "pub_payments_process_fineos_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-fineos"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "pub_payments_process_fineos_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-fineos-fineos-assume-policy"
  role   = aws_iam_role.pub_payments_process_fineos_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "pub_payments_process_fineos_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-fineos-extras"
  role   = aws_iam_role.pub_payments_process_fineos_task_role.id
  policy = data.aws_iam_policy_document.pub_payments_process_fineos_task_role_extras.json
}

data "aws_iam_policy_document" "pub_payments_process_fineos_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*"
    ]

    effect = "Allow"
  }

  # See /docs/api/ses.tf for full details on configuring SES permissions.
  statement {
    sid = "AllowSESSendEmail"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    condition {
      test     = "ForAllValues:StringLike"
      variable = "ses:Recipients"
      values = [
        var.dfml_project_manager_email_address,
        var.dfml_business_operations_email_address
      ]
    }

    resources = ["*"]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pub-payments-process-snapshot
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "pub_payments_process_fineos_reconciliation_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-snapshot"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "pub_payments_process_fineos_reconciliation_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-snapshot-fineos-assume-policy"
  role   = aws_iam_role.pub_payments_process_fineos_reconciliation_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "pub_payments_process_fineos_reconciliation_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-snapshot-extras"
  role   = aws_iam_role.pub_payments_process_fineos_reconciliation_task_role.id
  policy = data.aws_iam_policy_document.pub_payments_process_fineos_reconciliation_task_role_extras.json
}

data "aws_iam_policy_document" "pub_payments_process_fineos_reconciliation_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*"
    ]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pub-payments-create-pub-files
# (Use default task_executor execution role)
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "pub_payments_create_pub_files_task_role" {
  name               = "${local.app_name}-${var.environment_name}-pub-payments-create-pub-files"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "pub_payments_create_pub_files_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-create-pub-files-fineos-assume-policy"
  role   = aws_iam_role.pub_payments_create_pub_files_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "pub_payments_create_pub_files_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-pub-payments-create-pub-files-extras"
  role   = aws_iam_role.pub_payments_create_pub_files_task_role.id
  policy = data.aws_iam_policy_document.pub_payments_create_pub_files_task_role_extras.json
}

data "aws_iam_policy_document" "pub_payments_create_pub_files_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/pub",
      "${data.aws_s3_bucket.agency_transfer.arn}/pub/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses/*"
    ]

    effect = "Allow"
  }

  # See /docs/api/ses.tf for full details on configuring SES permissions.
  statement {
    sid = "AllowSESSendEmail"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    condition {
      test     = "ForAllValues:StringLike"
      variable = "ses:Recipients"
      values = [
        var.dfml_project_manager_email_address,
        var.dfml_business_operations_email_address
      ]
    }

    resources = ["*"]
    effect    = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pub-payments-process-pub-returns
# (Use default task_executor execution role)
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "pub_payments_process_pub_returns_task_role" {
  name               = "${local.app_name}-${var.environment_name}-pub-payments-process-pub-returns"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "pub_payments_process_pub_returns_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-pub-returns-fineos-assume-policy"
  role   = aws_iam_role.pub_payments_process_pub_returns_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "pub_payments_process_pub_returns_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-pub-payments-process-pub-returns-extras"
  role   = aws_iam_role.pub_payments_process_pub_returns_task_role.id
  policy = data.aws_iam_policy_document.pub_payments_process_pub_returns_task_role_extras.json
}

data "aws_iam_policy_document" "pub_payments_process_pub_returns_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }
  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/pub",
      "${data.aws_s3_bucket.agency_transfer.arn}/pub/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses/*"
    ]

    effect = "Allow"
  }

  # See /docs/api/ses.tf for full details on configuring SES permissions.
  statement {
    sid = "AllowSESSendEmail"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    condition {
      test     = "ForAllValues:StringLike"
      variable = "ses:Recipients"
      values = [
        var.dfml_project_manager_email_address,
        var.dfml_business_operations_email_address
      ]
    }

    resources = ["*"]
    effect    = "Allow"
  }
}

#####

resource "aws_iam_role" "pub_payments_copy_audit_report_task_role" {
  name               = "${local.app_name}-${var.environment_name}-pub-payments-copy-audit-report"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "pub_payments_copy_audit_report_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-pub-payments-copy-audit-report-extras"
  role   = aws_iam_role.pub_payments_copy_audit_report_task_role.id
  policy = data.aws_iam_policy_document.pub_payments_copy_audit_report_task_role_extras.json
}

data "aws_iam_policy_document" "pub_payments_copy_audit_report_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses/*"
    ]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pub-claimant-address-validation
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "pub_claimant_address_validation_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-claimant-address-validation"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "pub_claimant_address_validation_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-claimant-address-validation-fineos-assume-policy"
  role   = aws_iam_role.pub_claimant_address_validation_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "pub_claimant_address_validation_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-claimant-address-validation-extras"
  role   = aws_iam_role.pub_claimant_address_validation_task_role.id
  policy = data.aws_iam_policy_document.pub_claimant_address_validation_task_role_extras.json
}

data "aws_iam_policy_document" "pub_claimant_address_validation_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/pub",
      "${data.aws_s3_bucket.agency_transfer.arn}/pub/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses/*"
    ]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for pub-payments-process-1099-documents
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "pub_payments_process_1099_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "pub_payments_process_1099_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099-fineos-assume-policy"
  role   = aws_iam_role.pub_payments_process_1099_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "pub_payments_process_1099_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099-extras"
  role   = aws_iam_role.pub_payments_process_1099_task_role.id
  policy = data.aws_iam_policy_document.pub_payments_process_1099_task_role_extras.json
}

data "aws_iam_policy_document" "pub_payments_process_1099_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/pub",
      "${data.aws_s3_bucket.agency_transfer.arn}/pub/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit",
      "${data.aws_s3_bucket.agency_transfer.arn}/audit/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses",
      "${data.aws_s3_bucket.reports.arn}/dfml-responses/*"
    ]

    effect = "Allow"
  }
}

resource "aws_iam_role_policy" "pub_payments_process_1099_role_s3_access_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name = "${local.app_name}-${var.environment_name}-ecs-tasks-pub-payments-process-1099-s3_access-policy"
  role = aws_iam_role.pub_payments_process_1099_task_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:Get*",
          "s3:List*",
          "s3:PutObject"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.ecs_tasks_1099_bucket.arn}",
          "${aws_s3_bucket.ecs_tasks_1099_bucket.arn}/*"
        ]
      },
    ]
  })
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for fineos-import-iaww
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "fineos_import_iaww_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-iaww"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "fineos_import_iaww_task_fineos_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-iaww-fineos-assume-policy"
  role   = aws_iam_role.fineos_import_iaww_task_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "fineos_import_iaww_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-import-iaww-extras"
  role   = aws_iam_role.fineos_import_iaww_task_role.id
  policy = data.aws_iam_policy_document.fineos_import_iaww_task_role_extras.json
}

data "aws_iam_policy_document" "fineos_import_iaww_task_role_extras" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      data.aws_s3_bucket.reports.arn,
      "${data.aws_s3_bucket.reports.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "ReadWriteAccessToAgencyTransferBucket"
    actions = [
      "s3:ListBucket",
      "s3:Get*",
      "s3:List*",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/cps",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps/*",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports",
      "${data.aws_s3_bucket.agency_transfer.arn}/reports/*",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports",
      "${data.aws_s3_bucket.reports.arn}/dfml-reports/*"
    ]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for reductions-workflow
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "reductions_workflow_task_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "reductions_workflow_task_role_extras" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow-extras"
  role   = aws_iam_role.reductions_workflow_task_role.id
  policy = data.aws_iam_policy_document.reductions_workflow_task_role_extras.json
}

data "aws_iam_policy_document" "reductions_workflow_task_role_extras" {
  statement {
    sid    = "AllowListingOfBucket"
    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions",
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions/*",
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }

  statement {
    sid    = "AllowS3ReadOnBucket"
    effect = "Allow"

    actions = [
      "s3:Get*",
      "s3:List*"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions",
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions/*",
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }

  statement {
    sid    = "AllowS3WriteOnBucket"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions",
      "${data.aws_s3_bucket.agency_transfer.arn}/reductions/*",
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }

  statement {
    sid    = "AllowSESSendEmail"
    effect = "Allow"

    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    condition {
      test     = "ForAllValues:StringLike"
      variable = "ses:Recipients"
      values = [
        var.dfml_project_manager_email_address,
        var.dfml_business_operations_email_address,
        var.agency_reductions_email_address,
      ]
    }

    resources = ["*"]
  }
}

resource "aws_iam_role" "reductions_workflow_execution_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-reductions-wrkflw-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "reductions_workflow_execution_role_extras" {
  role       = aws_iam_role.reductions_workflow_execution_role.name
  policy_arn = aws_iam_policy.reductions_workflow_execution_role_extras.arn
}

resource "aws_iam_policy" "reductions_workflow_execution_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-ecs-tasks-reductions-workflow-execution-policy"
  description = "A clone of the standard execution role with extra SSM permissions for Reductions Workflow decryption keys."
  policy      = data.aws_iam_policy_document.reductions_workflow_execution_role_extras.json
}

data "aws_iam_policy_document" "reductions_workflow_execution_role_extras" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common/*",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "${local.ssm_arn_prefix}/${local.app_name}-comptroller/${var.environment_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin/*",
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}-comptroller/${var.environment_name}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin"
    ]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for S3 buckets for business intelligence (BI) data extracts
# ----------------------------------------------------------------------------------------------------------------------

data "aws_s3_bucket" "business_intelligence_tool" {
  bucket = "massgov-pfml-${var.environment_name}-business-intelligence-tool"
}

resource "aws_iam_role" "fineos_bucket_tool_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-bucket-tool"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

# We may not always have a value for `fineos_aws_iam_role_arn` and a policy has
# to list a resource, so make this part conditional with the count hack
resource "aws_iam_role_policy" "fineos_bucket_tool_assume_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-bucket-tool-assume-role-policy"
  role   = aws_iam_role.fineos_bucket_tool_role.id
  policy = data.aws_iam_policy_document.fineos_feeds_role_policy[0].json
}

resource "aws_iam_role_policy" "fineos_bucket_tool_role_policy" {
  count = var.fineos_aws_iam_role_arn == "" ? 0 : 1

  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-fineos-bucket-tool-role-policy"
  role   = aws_iam_role.fineos_bucket_tool_role.id
  policy = data.aws_iam_policy_document.fineos_bucket_tool_task_policy_document.json
}

data "aws_iam_policy_document" "fineos_bucket_tool_task_policy_document" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      data.aws_s3_bucket.business_intelligence_tool.arn
    ]

    effect = "Allow"
  }

  statement {
    sid = "AllowS3ReadOnBucket"
    actions = [
      "s3:Get*",
      "s3:List*"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/",
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      "${data.aws_s3_bucket.business_intelligence_tool.arn}/",
      "${data.aws_s3_bucket.business_intelligence_tool.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "AllowS3WriteOnBucket"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/",
      "${data.aws_s3_bucket.agency_transfer.arn}/*",
      "${data.aws_s3_bucket.business_intelligence_tool.arn}/",
      "${data.aws_s3_bucket.business_intelligence_tool.arn}/*"
    ]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for S3 buckets for SFTP (agency transfer) tool
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "sftp_tool_role" {
  name               = "${local.app_name}-${var.environment_name}-ecs-tasks-sftp-tool"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "sftp_tool_assume_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-sftp-tool-assume-role-policy"
  role   = aws_iam_role.sftp_tool_role.id
  policy = data.aws_iam_policy_document.sftp_tool_task_policy_document.json
}

resource "aws_iam_role_policy" "sftp_tool_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-ecs-tasks-sftp-tool-role-policy"
  role   = aws_iam_role.sftp_tool_role.id
  policy = data.aws_iam_policy_document.sftp_tool_task_policy_document.json
}

data "aws_iam_policy_document" "sftp_tool_task_policy_document" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn
    ]

    effect = "Allow"
  }

  statement {
    sid = "AllowS3ReadOnBucket"
    actions = [
      "s3:Get*",
      "s3:List*"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/",
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]

    effect = "Allow"
  }

  statement {
    sid = "AllowS3WriteOnBucket"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/",
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]

    effect = "Allow"
  }
}

resource "aws_iam_role" "sftp_tool_execution_role" {
  name               = "${local.app_name}-${var.environment_name}-sftp-tool-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "sftp_tool_execution_role_extras" {
  role       = aws_iam_role.sftp_tool_execution_role.name
  policy_arn = aws_iam_policy.sftp_tool_execution_role_extras.arn
}

resource "aws_iam_policy" "sftp_tool_execution_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-sftp-tool-execution-policy"
  description = "A clone of the standard execution role with extra SSM permissions for SFTP agency transfer."
  policy      = data.aws_iam_policy_document.sftp_tool_execution_role_extras.json
}

data "aws_iam_policy_document" "sftp_tool_execution_role_extras" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common/*",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "${local.ssm_arn_prefix}/${local.app_name}-comptroller/${var.environment_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin/*",
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}-comptroller/${var.environment_name}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin"
    ]
  }
}


# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for cps-errors-crawler
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "cps_errors_crawler_task_role" {
  name               = "${local.app_name}-${var.environment_name}-cps-errors-crawler-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "cps_errors_crawler_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-cps-errors-crawler-execution-role-policy"
  role   = aws_iam_role.cps_errors_crawler_task_role.id
  policy = data.aws_iam_policy_document.cps_errors_crawler_role_policy_document.json
}

data "aws_iam_policy_document" "cps_errors_crawler_role_policy_document" {
  statement {
    sid = "AllowListingOfBucket"
    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "cps-errors/received/",
        "cps-errors/received/*"
      ]
    }

    effect = "Allow"
  }

  statement {
    sid = "AllowS3ReadDeleteOnBucket"

    actions = [
      "s3:Get*",
      "s3:List*",
      "s3:DeleteObject"
    ]
    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/cps-errors/received",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps-errors/received/*"
    ]

    effect = "Allow"
  }
  statement {
    sid = "AllowS3WriteOnBucket"

    actions = [
      "s3:List*",
      "s3:PutObject",
      "s3:AbortMultipartUpload"
    ]

    resources = [
      "${data.aws_s3_bucket.agency_transfer.arn}/cps-errors/processed",
      "${data.aws_s3_bucket.agency_transfer.arn}/cps-errors/processed/*"
    ]

    effect = "Allow"
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for update-gender-data-from-rmv
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "update_gender_data_from_rmv_task_role" {
  name               = "${local.app_name}-${var.environment_name}-update-gender-data-from-rmv-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "update_gender_data_from_rmv_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-update-gender-data-from-rmv-role-policy"
  role   = aws_iam_role.update_gender_data_from_rmv_task_role.id
  policy = data.aws_iam_policy_document.update_gender_data_from_rmv.json
}

data "aws_iam_policy_document" "update_gender_data_from_rmv" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      var.rmv_client_certificate_binary_arn,
    ]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for evaluate-new-financial-eligibility
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "evaluate_new_financial_eligibility_task_role" {
  name               = "${local.app_name}-${var.environment_name}-new-financial-eligibility-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "evaluate_new_financial_eligibility_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-evaluate-new-financial-eligibility-role-policy"
  role   = aws_iam_role.evaluate_new_financial_eligibility_task_role.id
  policy = data.aws_iam_policy_document.evaluate_new_financial_eligibility.json
}

# Defined in infra/api/ and referenced here.
data "aws_cloudwatch_log_group" "service_logs" {
  name = "service/${local.app_name}-${var.environment_name}"
}

data "aws_iam_policy_document" "evaluate_new_financial_eligibility" {
  # Allow writing results to S3.
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "logs:StartQuery",
      "logs:GetLogEvents"
    ]
    resources = [
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export",
      "arn:aws:s3:::massgov-pfml-${var.environment_name}-execute-sql-export/*",
      "${data.aws_cloudwatch_log_group.service_logs.arn}:*",

    ]
  }

  # Allow reading API server logs from CloudWatch logs.
  statement {
    effect = "Allow"
    actions = [
      "logs:DescribeQueries",
      "logs:GetQueryResults"
    ]
    resources = [
      "*",
    ]
  }
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM role and policies for dua-import-employee-demographics
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role" "dua_employee_workflow_task_role" {
  name               = "${local.app_name}-${var.environment_name}-dua-employee-workflow-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy" "dua_employee_workflow_role_policy" {
  name   = "${local.app_name}-${var.environment_name}-dua-employee-workflow-task-role-policy"
  role   = aws_iam_role.dua_employee_workflow_task_role.id
  policy = data.aws_iam_policy_document.dua_employee_workflow.json
}

data "aws_iam_policy_document" "dua_employee_workflow" {
  # Allow writing results to S3.
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [
      data.aws_s3_bucket.agency_transfer.arn,
      "${data.aws_s3_bucket.agency_transfer.arn}/*"
    ]
  }
}

resource "aws_iam_role" "dua_employee_workflow_execution_role" {
  name               = "${local.app_name}-${var.environment_name}-dua-employee-workflow-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "dua_employee_workflow_execution_role_extras" {
  role       = aws_iam_role.dua_employee_workflow_execution_role.name
  policy_arn = aws_iam_policy.dua_employee_workflow_execution_role_extras.arn
}

resource "aws_iam_policy" "dua_employee_workflow_execution_role_extras" {
  name        = "${local.app_name}-${var.environment_name}-dua-employee-workflow-execution-policy"
  description = "A clone of the standard execution role with extra SSM permissions for DUA Employee Workflow decryption keys."
  policy      = data.aws_iam_policy_document.dua_employee_workflow_execution_role_extras.json
}

data "aws_iam_policy_document" "dua_employee_workflow_execution_role_extras" {
  # Allow ECS to log to Cloudwatch.
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]

    resources = [
      "${aws_cloudwatch_log_group.ecs_tasks.arn}:*"
    ]
  }

  # Allow ECS to authenticate with ECR and download images.
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]

    # ECS Fargate doesn't like it when you restrict the access to a single
    # repository. Instead, it needs access to all of them.
    resources = [
      "*"
    ]
  }

  # Allow ECS to access secrets from parameter store.
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common/*",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}/*",
      "${local.ssm_arn_prefix}/${local.app_name}-comptroller/${var.environment_name}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin/*",
    ]
  }

  statement {
    actions = [
      "ssm:GetParametersByPath",
    ]

    resources = [
      "${local.ssm_arn_prefix}/${local.app_name}/common",
      "${local.ssm_arn_prefix}/${local.app_name}/${var.environment_name}",
      "${local.ssm_arn_prefix}/${local.app_name}-comptroller/${var.environment_name}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/admin"
    ]
  }
}

