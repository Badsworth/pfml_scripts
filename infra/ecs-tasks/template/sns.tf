resource "aws_sns_topic" "task_failure" {
  name         = "mass-pfml-${var.environment_name}-task-failure"
  display_name = "PFML API Layer: Task Failure Alerts"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

resource "aws_cloudformation_stack" "sns_task_failure_topic_subscription" {
  for_each = toset(var.task_failure_email_address_list)

  name = "mass-pfml-${var.environment_name}-task-failure-subscription-${substr(md5(each.key), 0, 8)}"
  template_body = templatefile("${path.module}/json/cloudformation_sns_subscription.json.tpl",
    {
      sns_topic_arn = aws_sns_topic.task_failure.arn
      sns_email     = each.key
    }
  )

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}
