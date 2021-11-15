# Environment Variables

We configure the application by using [environment variables](https://12factor.net/config).

## Local Development

During local development, we specify environment variables through [docker-compose.yml](/api/docker-compose.yml).

```yaml
mass-pfml-api:
  ...
  environment:
    - ENVIRONMENT=local
    - DB_HOST=mass-pfml-db
    - DB_NAME=pfml
    - DB_USERNAME=pfml
    - DB_PASSWORD=secret123
```

When updating these variables, you'll need to run `make build` 
in order to rebuild your container and pick up the new values.

### Overriding AWS credentials

To use your AWS credentials locally:

1. Run `aws sso login`
1. Override the container's AWS credentials path in `docker-compose.override.yml` (there's a commented line showing an example)
1. Set the `AWS_PROFILE` in `docker-compose.yml` to the AWS profile you want to use
1. Rerun `make build`

## Deployed Environments

In deployed environments, variables are pulled in through AWS Elastic Container Service (ECS) 
as listed in the [container definition](/infra/api/template/container_definitions.json). 
Non-sensitive values are encoded into the definition when Terraform generates it:

```json
"environment": [
  { "name": "ENVIRONMENT", "value": "${environment_name}" },
  { "name": "DB_HOST", "value": "${db_host}" },
  { "name": "DB_NAME", "value": "${db_name}" },
  { "name": "DB_USERNAME", "value": "${db_username}" },
  { ... }
]
```

...and sensitive values are pulled in from AWS SSM Parameter Store when the container starts:

```json
"secrets": [
  { "name": "DB_PASSWORD", "valueFrom": "/service/${app_name}/${environment_name}/db-password" },
  { "name": "NEW_RELIC_LICENSE_KEY", "valueFrom": "/service/${app_name}/common/newrelic-license-key" },
  { ... }
]
```

To view or update non-sensitive values in the container definition file, 
set them in the `container_definitions` resource in [service.tf](/infra/api/template/service.tf).

To recap for non-sensitive values:

1. If it's a variable that should be configured explicitly for each environment:
    1. Add new variable to the [API template
       variables.tf](/infra/api/template/variables.tf)
    2. Set the new variables in each [environment
       configuration](/infra/api/environments)
2. Add and set variable in [service.tf](/infra/api/template/service.tf), either
   referring to variables from step 1 or to other Terraform resources.
3. Use variable set in service.tf to set environment variable in
   [container_definitions.json](/infra/api/template/container_definitions.json)

To view or update sensitive values:

1. Go to the key in the [AWS Systems Manager/Parameter Store
   console](https://console.aws.amazon.com/systems-manager/parameters?region=us-east-1).
2. Create or update the sensitive string with the default KMS key, matching the
   `valueFrom` field that you specify in the container definition above.

In both cases, the application will need to be redeployed before any changes to the environment variables are picked up.
