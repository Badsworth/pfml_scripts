resource "aws_sns_topic" "task_failure" {
  name              = "massgov-pfml-${var.environment_name}-task-failure"
  display_name      = "PFML API Layer: Task Failure Alerts"
  kms_master_key_id = data.aws_kms_key.env_kms_key.id
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_sns_topic_subscription" "sns_task_failure_topic_subscription" {
  for_each               = toset(var.task_failure_email_address_list)
  topic_arn              = aws_sns_topic.task_failure.arn
  protocol               = "email-json"
  endpoint               = each.key
  endpoint_auto_confirms = true
}