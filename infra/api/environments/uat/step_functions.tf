#
# Terraform configuration for AWS Step Functions.
#

#
# State machine for daily DOR FINEOS ETL.
#
locals {
  dor_fineos_etl_definition = templatefile("${path.module}/step_function/dor_fineos_etl.json",
    {
      app_name         = "pfml-api"
      cluster_arn      = data.aws_ecs_cluster.uat.arn
      environment_name = local.environment_name
      security_group   = data.aws_security_group.tasks.id
      subnet_1         = tolist(data.aws_subnet_ids.vpc_app.ids)[0]
      subnet_2         = tolist(data.aws_subnet_ids.vpc_app.ids)[1]
  })
}

# This is defined in ecs-tasks/template/security_groups.tf and referenced by name here.
data "aws_security_group" "tasks" {
  name = "pfml-api-uat-tasks"
}
