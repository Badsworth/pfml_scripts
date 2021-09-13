# Feature Flags

This directory contains feature flag YAML files which are exposed through the Paid Leave API. The files on the main branch represent the current state of flags managed through this system.

Note that this system is not currently in wide use. See the following pages for information on how feature flags are commonly managed:

- [API Environment Variable Configuration](../docs/api/environment-variables.md)
- [Portal Build-time Feature Flags/Environment Variables](../docs/portal/feature-flags.md)

## Modifying Flags

Each flag is defined with the following keys:

```yaml
my_flag_name:
  enabled: <0 or 1>
  start: <Optional ISO 8601 timestamp>
  end: <Optional ISO 8601 timestamp>
  options:
    <Optional, custom options dict>
```

`start` and `end` can be defined together or separately to allow flags to be enabled indefinitely, or enabled with an expiry.

```yaml
# Enable flag starting on 7/30/2021, without an end date
my_flag_name:
  enabled: 1
  start: 2021-07-30T04:00:00+00:00
```

## Deployment

Changes to these files in the main branch will automatically trigger the [Feature Flags Sync workflow](../.github/workflows/feature-flags-sync.yml) on Github Actions, pushing the updated yaml files to the appropriate folders in S3 (`massgov-pfml-{env}-feature-gate/features.yaml`).

The Paid Leave API periodically updates its in-memory cache of the feature flags and serves them through the [/flags](../api/massgov/pfml/api/flags.py) endpoint. The Paid Leave Portal caches these flags as needed and sets them in [appLogic.featureFlags.flags](../portal/src/hooks/useAppLogic.js). The API request is cached for five minutes and only executed once for every full page request (not on react render/re-render).

It may take up to 20 minutes for the portal to read the updated feature flags due to the API in-memory expiry and the browser-side expiry.
