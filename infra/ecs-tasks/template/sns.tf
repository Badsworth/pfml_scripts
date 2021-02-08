resource "aws_sns_topic" "task_failure" {
  name         = "mass-pfml-${var.environment_name}-task-failure"
  display_name = "PFML API Layer: Task Failure Alerts"
  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}

data "template_file" "cf_sns_task_failure_subscription" {
  for_each = toset(var.task_failure_email_address_list)

  template = file("${path.module}/json/cloudformation_sns_subscription.json.tpl")
  vars = {
    sns_topic_arn = aws_sns_topic.task_failure.arn
    sns_email     = each.key
  }
}

resource "aws_cloudformation_stack" "sns_task_failure_topic_subscription" {
  for_each = toset(var.task_failure_email_address_list)

  name          = "mass-pfml-${var.environment_name}-task-failure-subscription-${substr(md5(each.key), 0, 8)}"
  template_body = data.template_file.cf_sns_task_failure_subscription[each.key].rendered

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
  })
}
