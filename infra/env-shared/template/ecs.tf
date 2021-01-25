# ECS cluster for running applications in an environment.
#
# Applications within this cluster are not actually tied
# to a VPC/environment, but we separate them to improve
# organization and simplify lookups.
resource "aws_ecs_cluster" "cluster" {
  name = var.environment_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(module.constants.common_tags, {
    environment = module.constants.environment_tags[var.environment_name]
    "SMX:Asset" = "v1:${var.environment_name}:${module.constants.smartronix_environment_tags[var.environment_name]}:ECS:PFML:Advanced:None"
  })
}
