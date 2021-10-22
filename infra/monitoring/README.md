# Monitoring Infrastructure

Application monitors and alerts are managed via Terraform in this folder. This folder accounts for monitoring across all environments.

## Key Components

### Pagerduty Schedules and Escalation Policies

Base on-call schedules and escalation policies are set up using Terraform in the pagerduty files. Specific changes to personnel and week-to-week schedules are managed through the Pagerduty UI by on-call engineers and delivery managers.

### New Relic and Cloudwatch Alerts

An assortment of New Relic and Cloudwatch alerts are generated for each environment in [alarms.tf](./alarms.tf). We upload shared API keys to AWS Parameter Store and pull them down as needed in [newrelic_api_keys.tf](./newrelic_api_keys.tf) for running terraform to avoid requiring every engineer from managing their own New Relic credentials locally.

### ECS Failure Monitor Lambda

This module launches a cross-environment lambda which listens for ECS tasks that failed to start, and sends a notification to Slack. This mainly exists to notify us of any tasks that were broken by a code change, notably for missing Parameter Store secrets.

### DUA Daily Email Lambda

This module also launches a lambda which runs on a daily basis. The lambda pulls the previous day's DUA_DFML reporting csv, compresses it, and sends it to email recipients.

Usually, the background DUA job would send the file automatically; however, when the file is too big, it cannot be sent through SES. See: [OPSS-120](https://lwd.atlassian.net/browse/OPSS-120).

## Testing

For more details about making and testing changes, see [Making Changes to Alerts](../../docs/infra/5-making-changes-to-alerts.md).

## Deployment

Changes to this module are automatically deployed by Github Actions when a pull request is merged to the main branch. See [Monitoring Deploy](https://github.com/EOLWD/pfml/actions/workflows/monitoring-deploy.yml).

