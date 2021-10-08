# Environment Management

### Setting up a new environment

🔗 See [docs/creating-environments.md](../docs/creating-environments.md) for instructions on how to create a new environment.

## tfstate files

Each environment for a component has a `.tfstate` file that is stored in S3 and synchronized using a DynamoDB lock table.
Terraform relies on this state file for every command and must acquire the DynamoDB lock in order to use it, so only one person or system can run a terraform command at a time.

```
S3
└── massgov-pfml-aws-account-mgmt
    └── terraform
        └── aws.tfstate
        └── monitoring.tfstate
└── massgov-pfml-test-env-mgmt
    └── terraform
        └── env-shared.tfstate
        └── portal.tfstate
        └── api.tfstate
        └── ecs-tasks.tfstate
└── ...
```

Note that modules like `constants`, `modules/ecs_task_scheduler`, etc. are not deployed on their own and therefore do not have their own tfstate files. These modules are used within deployable modules like `monitoring` and `api`.
