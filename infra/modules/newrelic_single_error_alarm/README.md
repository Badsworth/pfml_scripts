# newrelic_single_error_alarm

Creates a New Relic alarm that is set off by any result from the given NRQL query.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 0.13 |

## Providers

| Name | Version |
|------|---------|
| newrelic | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| enabled | Whether the alarm is enabled or not | `bool` | `true` | no |
| name | Name of the alarm | `any` | n/a | yes |
| nrql | NRQL query to trigger an alarm on | `any` | n/a | yes |
| policy\_id | New Relic policy for the alarm to attach to | `any` | n/a | yes |
| runbook\_url | URL of the runbook for this alarm | `any` | `null` | no |

## Outputs

No output.

