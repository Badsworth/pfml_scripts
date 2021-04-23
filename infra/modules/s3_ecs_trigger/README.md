Generates a lambda that triggers an ECS task, and provides permissions to be run by S3. 

The S3 event notification trigger must be configured outside of this module using the lambda_arn output.

## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| archive | n/a |
| aws | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| app\_subnet\_ids | Subnets to run the task in | `list(any)` | n/a | yes |
| ecs\_task\_definition\_family | ECS task definition family | `string` | n/a | yes |
| ecs\_task\_executor\_role | Execution role that must be passed to the ECS task | `string` | n/a | yes |
| ecs\_task\_role | Task role that must be passed to the ECS task | `string` | `null` | no |
| environment\_name | Name of the environment to run in | `string` | n/a | yes |
| s3\_bucket\_arn | ARN of the S3 bucket that will be triggering this lambda | `string` | n/a | yes |
| security\_group\_ids | Security groups for the ECS task to run with | `list(any)` | n/a | yes |
| task\_name | Name of the task | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| lambda\_arn | ARN of the generated lambda |

