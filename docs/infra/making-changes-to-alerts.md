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

```tf
$ terraform apply --target module.alarms_api[\"test\"] --target module.alarms_portal[\"test\"]
```

The terraform plan should indicate that _only_ test alarms will be updated.
