## ecs_task_scheduler

Runs an ECS Fargate task on a given schedule.

## Examples

```
module "register_leave_admins_with_fineos_scheduler" {
  source     = "../../modules/ecs_task_scheduler"
  is_enabled = var.enable_register_admins_job

  task_name           = "register-leave-admins-with-fineos"
  schedule_expression = "rate(15 minutes)"
  environment_name    = var.environment_name

  cluster_arn        = data.aws_ecs_cluster.cluster.arn
  app_subnet_ids     = var.app_subnet_ids
  security_group_ids = [aws_security_group.tasks.id]

  ecs_task_definition_arn    = aws_ecs_task_definition.ecs_tasks["register-leave-admins-with-fineos"].arn
  ecs_task_definition_family = aws_ecs_task_definition.ecs_tasks["register-leave-admins-with-fineos"].family
  ecs_task_executor_role     = aws_iam_role.task_executor.arn
  ecs_task_role              = aws_iam_role.register_admins_task_role.arn
}
```

## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| aws | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| app\_subnet\_ids | Subnets to run the task in | `list` | n/a | yes |
| cluster\_arn | ECS cluster to run the task in | `string` | n/a | yes |
| ecs\_task\_definition\_arn | Specific ECS task definition version to launch | `string` | n/a | yes |
| ecs\_task\_definition\_family | ECS task definition family | `string` | n/a | yes |
| ecs\_task\_executor\_role | Execution role that must be passed to the ECS task | `string` | n/a | yes |
| ecs\_task\_role | Task role that must be passed to the ECS task | `string` | `null` | no |
| environment\_name | Name of the environment to run in | `string` | n/a | yes |
| input | Valid JSON text passed to the target as input | `string` | `null` | no |
| is\_enabled | whether to enable the schedule or not | `bool` | n/a | yes |
| schedule\_expression | Schedule to follow for running the task | `string` | n/a | yes |
| security\_group\_ids | Security groups for the task to attach | `list` | n/a | yes |
| task\_name | Name of the task | `string` | n/a | yes |

## Outputs

No output.

