#
# Terraform configuration for AWS Step Functions.
#

#
# State machine for daily DOR FINEOS ETL.
#

# make a file for this
data "aws_ecs_cluster" "test" {
  cluster_name = "test"
}

locals {
  dor_fineos_etl_definition = templatefile("${path.module}/step_function/dor_fineos_etl.json",
    {
      app_name              = "pfml-api"
      cluster_arn           = data.aws_ecs_cluster.test.arn
      environment_name      = "test"
      security_group        = data.aws_security_group.tasks.id
      subnet_1              = tolist(data.aws_subnet_ids.vpc_app.ids)[0]
      subnet_2              = tolist(data.aws_subnet_ids.vpc_app.ids)[1]
      sns_failure_topic_arn = data.aws_sns_topic.task_failure.arn

      task_failure_notification_enabled = true
  })
}

# This is defined in ecs-tasks/template/security_groups.tf and referenced by name here.
data "aws_security_group" "tasks" {
  name = "pfml-api-test-tasks"
}

# This is defined in ecs-tasks/template/sns.tf and referenced by name here.
data "aws_sns_topic" "task_failure" {
  name = "mass-pfml-test-task-failure"
}
