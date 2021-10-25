# Making Changes to Alerts

Application monitors and alerts are managed via Terraform in the `infra/monitoring` folder. This folder accounts for monitoring across all environments and is automatically deployed when changes are merged into the main branch.

## Alarm Modules

The core code for building Cloudwatch and New Relic alerts are stored in re-usable modules under the following directories:

- [infra/modules/alarms_api](../../infra/modules/alarms_api)
- [infra/modules/alarms_portal](../../infra/modules/alarms_portal)

## Testing Monitoring Changes in TEST

It's often desirable to test changes to monitoring in the TEST environment during feature development. Since monitoring changes for all environments are combined into a single configuration, terraform actions must specifically target certain resources.

Almost all alarms are built through the [infra/modules/alarms_api](../../infra/modules/alarms_api) and [infra/modules/alarms_portal](../../infra/modules/alarms_portal) modules, which are used within [infra/monitoring/alarms.tf](../../infra/monitoring/alarms.tf):

```tf
module "alarms_api" {
  for_each = toset(local.environments)
  source   = "../modules/alarms_api"
  
  ...
}
```

To update the set of alarms for a single environment, go into the `infra/monitoring` root module and target the alarms module with a particular key:

```sh
$ terraform apply --target module.alarms_api[\"test\"] --target module.alarms_portal[\"test\"]

# or

$ terraform apply -target 'module.alarms_api["test"]' -target 'module.alarms_portal["test"]'
```

The terraform plan should indicate that _only_ test alarms will be updated.

## Resources

Here is a list of external documentation resources that could prove useful while making changes:

- [Building New Relic Alarms - Kevin Yeh - Confluence](https://lwd.atlassian.net/wiki/spaces/~127922489/pages/1406468351/Building+New+Relic+Alarms)
- [Streaming alerts: key terms and concepts | New Relic Documentation](https://docs.newrelic.com/docs/alerts-applied-intelligence/new-relic-alerts/get-started/streaming-alerts-key-terms-concepts/)
- [Create NRQL alert conditions | New Relic Documenation](https://docs.newrelic.com/docs/alerts-applied-intelligence/new-relic-alerts/alert-conditions/create-nrql-alert-conditions/)
- [Docs overview | newrelic/newrelic | Terraform Registry](https://registry.terraform.io/providers/newrelic/newrelic/latest/docs)

## Getting Access

The documentation here assumes the reader has access to AWS and has Terraform configured locally. Additionally, it is useful to have access to New Relic to view and test queries. View the [Tools Access](https://lwd.atlassian.net/wiki/spaces/DD/pages/142049579/Tools+Access) documentation for instructions on how to get access, then see the [First Time Setup](./1-first-time-setup.md) for setup instructions.
