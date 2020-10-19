# DOR Import
This is the ECS task formerly known as the DOR Data Import Lambda Function.

Please refer to the shared README at `api/lambdas/README.md` for shared build and release commands.
Please refer to the other shared README at `infra/ecs-tasks/template/tasks.tf` for IaC and container configuration.

**NB:** This task began life as a lambda. It was migrated to ECS in order to circumvent
the memory, CPU, and total-runtime limits that AWS imposes on all lambdas.

## Generating Mock files
- Generate mock DOR export files: `make generate`
- Generate with specific number of employers (employees = employer * 15): `make generate EMPLOYER_COUNT=2000`
