# Newrelic Endpoint Error Rates

Generate a set of error rate alarms for endpoints in a given environment.

## Providers

| Name | Version |
|------|---------|
| newrelic | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| endpoint\_filter\_nrql | WHERE filter for endpoint based on Span attributes | `string` | n/a | yes |
| environment\_name | Name of the environment | `string` | n/a | yes |
| name | Name of the alarm | `string` | n/a | yes |

## Outputs

No output.

