# NOTE: There can only be one S3 bucket notification resource per bucket.
#
# This file sets up triggers to run ECS tasks based off of S3 events. However,
# this is not natively possible, so this actually happens in two steps:
#
# 1. A lambda is created using the s3_ecs_trigger module
# 2. S3 Bucket notifications are set up to trigger the lambda based off specified events
#
# The lambda will run the specified ECS task when triggered.
#

module "trigger_sharepoint_pub" {
  source = "../../modules/s3_ecs_trigger"

  environment_name   = var.environment_name
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  task_name                  = "pub-payments-create-pub-files"
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-payments-create-pub-files"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.pub_payments_create_pub_files_task_role.arn
  s3_bucket_arn              = data.aws_s3_bucket.reports.arn
}

module "trigger_agency_transfer_pub" {
  source = "../../modules/s3_ecs_trigger"

  environment_name   = var.environment_name
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  task_name                  = "pub-payments-process-pub-returns"
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["pub-payments-process-pub-returns"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.pub_payments_process_pub_returns_task_role.arn
  s3_bucket_arn              = data.aws_s3_bucket.agency_transfer.arn
}

resource "aws_s3_bucket_notification" "sharepoint_pub_notifications" {
  count  = var.enable_pub_automation_create_pub_files ? 1 : 0
  bucket = data.aws_s3_bucket.reports.id

  lambda_function {
    lambda_function_arn = module.trigger_sharepoint_pub.lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "dfml-responses"
  }
}

resource "aws_s3_bucket_notification" "agency_transfer_pub_notifications" {
  count  = var.enable_pub_automation_process_returns ? 1 : 0
  bucket = data.aws_s3_bucket.agency_transfer.id

  lambda_function {
    lambda_function_arn = module.trigger_agency_transfer_pub.lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "pub/inbound/"
    filter_suffix       = ".OK"
  }
}
